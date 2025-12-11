"""Pydantic models for Ansible roles."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class RoleMetadata(BaseModel):
    """Role metadata from meta/main.yml (galaxy_info section).

    Attributes:
        author: Role author name
        company: Company or organization name
        license: License identifier (e.g., 'MIT', 'Apache-2.0')
        min_ansible_version: Minimum required Ansible version
        platforms: List of supported platforms with versions
        galaxy_tags: Tags for Ansible Galaxy
        dependencies: List of role dependencies
        description: Role description
    """

    author: Optional[str] = None
    company: Optional[str] = None
    license: str = "MIT"
    min_ansible_version: str = "2.9"
    platforms: List[Dict[str, Any]] = Field(default_factory=list)
    galaxy_tags: List[str] = Field(default_factory=list)
    dependencies: List[Any] = Field(default_factory=list)
    description: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "author": "John Doe",
                "company": "Example Corp",
                "license": "MIT",
                "min_ansible_version": "2.10",
                "platforms": [{"name": "Ubuntu", "versions": ["20.04", "22.04"]}],
                "galaxy_tags": ["web", "nginx"],
                "dependencies": [],
            }
        }
    }


class RoleTask(BaseModel):
    """Single task in an Ansible role.

    Attributes:
        name: Task name (can be 'Unnamed' if not specified in the task)
        module: Ansible module used (e.g., 'apt', 'copy')
        file: File where task is defined
        line_number: Line number in file
        description: Task description from comments
        when: Conditional expression
        notify: List of handlers to notify
        tags: List of task tags

    Note:
        If a task has no name in the YAML, it will be set to 'Unnamed' by
        process_special_task_keys(). The extract_task_name_from_module()
        function can create more meaningful composed names (e.g., "apt: nginx")
        when needed for display purposes.
    """

    name: str = "Unnamed"
    module: str = "unknown"
    file: str = "main.yml"
    line_number: int = 0
    description: Optional[str] = None
    when: Optional[str] = None
    notify: Optional[List[str]] = None
    tags: List[str] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Install nginx package",
                "module": "apt",
                "file": "main.yml",
                "line_number": 15,
                "description": "Installs nginx web server",
                "when": "ansible_os_family == 'Debian'",
                "notify": ["restart nginx"],
            }
        }
    }


class RoleVariable(BaseModel):
    """Variable defined in role defaults or vars.

    Attributes:
        name: Variable name
        value: Variable value (any type)
        type: Variable type name
        description: Variable description from comments
        required: Whether variable is required
        choices: List of valid choices
        title: Variable title/label
        line: Line number in file
    """

    name: str
    value: Any = None
    type: str = "str"
    description: Optional[str] = None
    required: bool = False
    choices: Optional[List[Any]] = None
    title: Optional[str] = None
    line: int = 0

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate variable name is not empty."""
        if not v or not v.strip():
            raise ValueError("Variable name cannot be empty")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "nginx_port",
                "value": 80,
                "type": "int",
                "description": "Port for nginx to listen on",
                "required": False,
                "choices": [80, 443, 8080],
            }
        }
    }


class Role(BaseModel):
    """Ansible role representation with full metadata.

    Attributes:
        name: Role name
        path: Path to role directory
        defaults: Default variables by file
        vars: Role variables by file
        tasks: List of tasks by file
        handlers: List of handlers
        meta: Role metadata from meta/main.yml
        argument_specs: Argument specifications
        repository: Git repository URL
        repository_type: Repository type (github, gitlab, gitea)
        repository_branch: Repository branch name
        belongs_to_collection: Collection info if role is part of collection
        docsible: Docsible metadata from .docsible file
        playbook: Playbook information
    """

    name: str
    path: Path
    defaults: List[Dict[str, Any]] = Field(default_factory=list)
    vars: List[Dict[str, Any]] = Field(default_factory=list)
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    handlers: List[Dict[str, Any]] = Field(default_factory=list)
    meta: Optional[Dict[str, Any]] = None
    argument_specs: Optional[Dict[str, Any]] = None
    repository: Optional[str] = None
    repository_type: Optional[str] = "github"
    repository_branch: Optional[str] = "main"
    belongs_to_collection: Optional[Dict[str, str]] = None
    docsible: Optional[Dict[str, Any]] = None
    playbook: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate role name is not empty."""
        if not v or not v.strip():
            raise ValueError("Role name cannot be empty")
        return v.strip()

    @field_validator("path")
    @classmethod
    def path_exists(cls, v: Path) -> Path:
        """Validate role path exists."""
        if not v.exists():
            logger.warning(f"Role path does not exist: {v}")
        return v

    def get_all_tasks(self) -> List[RoleTask]:
        """Get all tasks from all task files.

        Returns:
            List of RoleTask objects

        Example:
            >>> role = Role(name='my_role', path=Path('.'))
            >>> tasks = role.get_all_tasks()
            >>> len(tasks)
            10
        """
        all_tasks = []
        for task_file in self.tasks:
            for task_data in task_file.get("tasks", []):
                try:
                    task = RoleTask(**task_data)
                    all_tasks.append(task)
                except Exception as e:
                    logger.warning(f"Failed to parse task: {e}")
        return all_tasks

    def get_all_variables(self) -> List[RoleVariable]:
        """Get all variables from defaults and vars.

        Returns:
            List of RoleVariable objects

        Example:
            >>> role = Role(name='my_role', path=Path('.'))
            >>> variables = role.get_all_variables()
            >>> len(variables)
            5
        """
        all_vars = []

        # Get defaults
        for defaults_file in self.defaults:
            for var_name, var_data in defaults_file.get("data", {}).items():
                try:
                    var = RoleVariable(name=var_name, **var_data)
                    all_vars.append(var)
                except Exception as e:
                    logger.warning(f"Failed to parse variable {var_name}: {e}")

        # Get vars
        for vars_file in self.vars:
            for var_name, var_data in vars_file.get("data", {}).items():
                try:
                    var = RoleVariable(name=var_name, **var_data)
                    all_vars.append(var)
                except Exception as e:
                    logger.warning(f"Failed to parse variable {var_name}: {e}")

        return all_vars

    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "name": "nginx",
                "path": "/roles/nginx",
                "repository": "https://github.com/example/ansible-nginx",
                "repository_type": "github",
                "repository_branch": "main",
            }
        },
    }
