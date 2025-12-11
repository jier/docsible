"""Pydantic models for Docsible configuration."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class StructureConfig(BaseModel):
    """Ansible project structure configuration.

    Defines directory names and file patterns for flexible project layouts.

    Attributes:
        defaults_dir: Directory name for default variables
        vars_dir: Directory name for role variables
        tasks_dir: Directory name for tasks
        meta_dir: Directory name for metadata
        handlers_dir: Directory name for handlers
        templates_dir: Directory name for templates
        files_dir: Directory name for files
        library_dir: Directory name for custom modules
        roles_dir: Directory name for roles
        meta_file: Name of main metadata file
        yaml_extensions: List of YAML file extensions
    """

    defaults_dir: str = "defaults"
    vars_dir: str = "vars"
    tasks_dir: str = "tasks"
    meta_dir: str = "meta"
    handlers_dir: str = "handlers"
    templates_dir: str = "templates"
    files_dir: str = "files"
    library_dir: str = "library"
    roles_dir: str = "roles"
    meta_file: str = "main"
    lookup_plugins_dir: str = "lookup_plugins"
    test_playbook: str = "tests/test.yml"
    # Optional support
    # filter_plugins_dir: str = "filter_plugins"
    # module_utils_dir: str = "module_utils"

    argument_specs_file: str = "argument_specs"
    yaml_extensions: List[str] = Field(default_factory=lambda: [".yml", ".yaml"])

    @field_validator(
        "defaults_dir",
        "vars_dir",
        "tasks_dir",
        "meta_dir",
        "handlers_dir",
        "templates_dir",
        "files_dir",
        "library_dir",
        "roles_dir",
    )
    @classmethod
    def validate_dir_name(cls, v: str) -> str:
        """Ensure directory names don't start or end with slashes.

        Args:
            v: Directory name to validate

        Returns:
            Validated directory name

        Raises:
            ValueError: If directory name starts or ends with slash
        """
        if v.startswith("/") or v.endswith("/"):
            raise ValueError(
                f"Directory name '{v}' should not start or end with '/'. "
                "Use relative paths without leading/trailing slashes."
            )
        return v

    @field_validator("yaml_extensions")
    @classmethod
    def validate_extensions(cls, v: List[str]) -> List[str]:
        """Ensure YAML extensions start with a dot.

        Args:
            v: List of file extensions

        Returns:
            Validated list of extensions

        Raises:
            ValueError: If any extension doesn't start with a dot
        """
        for ext in v:
            if not ext.startswith("."):
                raise ValueError(
                    f"File extension '{ext}' must start with a dot (e.g., '.yml')"
                )
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "defaults_dir": "defaults",
                "vars_dir": "vars",
                "tasks_dir": "tasks",
                "meta_dir": "meta",
                "handlers_dir": "handlers",
            }
        }
    }


class DocsibleConfig(BaseModel):
    """Docsible project configuration from .docsible.yml file.

    Attributes:
        description: Functional description of the role/collection
        requester: Person who requested this automation
        users: Target users of this automation
        dt_dev: Development date
        dt_prod: Production deployment date
        dt_update: Last documentation update date
        version: Version number
        time_saving: Estimated time savings
        category: Primary category
        subCategory: Sub-category for classification
        aap_hub: AAP Hub availability status
        automation_kind: Type of automation
        critical: Critical system indicator
        structure: Custom structure configuration
    """

    description: Optional[str] = None
    requester: Optional[str] = None
    users: Optional[str] = None
    dt_dev: Optional[str] = None
    dt_prod: Optional[str] = None
    dt_update: Optional[str] = None
    version: Optional[str] = None
    time_saving: Optional[str] = None
    category: Optional[str] = None
    subCategory: Optional[str] = None
    aap_hub: Optional[str] = None
    automation_kind: Optional[str] = None
    critical: Optional[str] = None
    structure: Optional[StructureConfig] = None

    @field_validator("structure", mode="before")
    @classmethod
    def parse_structure(cls, v: Any) -> Optional[StructureConfig]:
        """Parse structure config from dict if needed."""
        if v is None:
            return None
        if isinstance(v, StructureConfig):
            return v
        if isinstance(v, dict):
            return StructureConfig(**v)
        raise ValueError("structure must be a dict or StructureConfig")

    @classmethod
    def from_file(cls, file_path: Path) -> "DocsibleConfig":
        """Load configuration from .docsible.yml file.

        Args:
            file_path: Path to .docsible.yml file

        Returns:
            DocsibleConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid

        Example:
            >>> config = DocsibleConfig.from_file(Path('.docsible.yml'))
            >>> print(config.description)
            'My role description'
        """
        import yaml

        if not file_path.exists():
            logger.warning(f"Config file not found: {file_path}")
            return cls()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        except Exception as e:
            logger.error(f"Failed to load config from {file_path}: {e}")
            raise ValueError(f"Invalid config file: {e}")

    def to_file(self, file_path: Path) -> None:
        """Save configuration to .docsible.yml file.

        Args:
            file_path: Path where to save the config file

        Example:
            >>> config = DocsibleConfig(description='My role')
            >>> config.to_file(Path('.docsible.yml'))
        """
        import yaml

        try:
            # Convert to dict, excluding None values
            data = self.model_dump(exclude_none=True)

            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"Config saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {file_path}: {e}")
            raise

    model_config = {
        "json_schema_extra": {
            "example": {
                "description": "Nginx web server role",
                "requester": "DevOps Team",
                "users": "Web Developers",
                "version": "1.0.0",
                "category": "Web Servers",
                "subCategory": "Reverse Proxy",
            }
        }
    }
