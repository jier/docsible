"""Builder for role information dictionary.

Extracts and processes all role components into a structured dictionary.
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from docsible.commands.document_role.models import ProcessingConfig, RepositoryConfig
from docsible.renderers.tag_manager import manage_docsible_file_keys
from docsible.utils.git import get_repo_info
from docsible.utils.mermaid import generate_mermaid_playbook
from docsible.utils.project_structure import ProjectStructure
from docsible.utils.special_tasks_keys import process_special_task_keys
from docsible.utils.yaml import (
    get_task_comments,
    get_task_line_numbers,
    get_task_line_ranges,
    load_yaml_files_from_dir_custom,
    load_yaml_generic,
)

logger = logging.getLogger(__name__)


class RoleInfoBuilder:
    """Builds comprehensive role information dictionary.

    Orchestrates extraction of metadata, variables, tasks, handlers,
    and playbook information from a role directory.

    Attributes:
        project_structure: ProjectStructure instance for path resolution
    """

    def __init__(self, project_structure: ProjectStructure | None = None):
        """Initialize RoleInfoBuilder.

        Args:
            project_structure: Optional ProjectStructure instance.
                If None, will be created from role_path during build().
        """
        self.project_structure = project_structure

    def build(
        self,
        role_path: Path,
        playbook_content: str | None,
        processing: ProcessingConfig,
        repository: RepositoryConfig,
        belongs_to_collection: dict | None = None,
    ) -> dict:
        """Build complete role information dictionary.

        Args:
            role_path: Path to role directory
            playbook_content: Optional playbook YAML content
            processing: Processing configuration (comments, task_line, etc.)
            repository: Repository configuration (url, type, branch)
            belongs_to_collection: Optional collection info if part of collection

        Returns:
            Dictionary with complete role information including:
            - name, defaults, vars, tasks, handlers, meta
            - playbook info (content, graph, dependencies)
            - repository info, argument specs, docsible metadata
        """
        # Initialize project structure if not provided
        if self.project_structure is None:
            self.project_structure = ProjectStructure(str(role_path))

        role_name = role_path.name

        # Build components
        meta_info = self._build_meta_info(role_path, processing.no_docsible)
        vars_info = self._build_vars_info(role_path)
        tasks_info = self._build_tasks_info(role_path, processing)
        handlers_info = self._build_handlers_info(role_path)
        playbook_info = self._build_playbook_info(
            playbook_content, role_name, processing.no_docsible
        )
        repo_info = self._build_repository_info(role_path, repository)
        argument_specs = self._get_argument_specs(role_path)

        # Combine all components
        return {
            "name": role_name,
            **vars_info,
            **tasks_info,
            **handlers_info,
            **meta_info,
            **playbook_info,
            **repo_info,
            "belongs_to_collection": belongs_to_collection,
            "argument_specs": argument_specs,
        }

    def _build_meta_info(self, role_path: Path, no_docsible: bool) -> dict:
        """Extract metadata and docsible configuration.

        Args:
            role_path: Path to role directory
            no_docsible: Whether to skip .docsible file handling

        Returns:
            Dictionary with 'meta' and 'docsible' keys
        """
        assert self.project_structure is not None, "project_structure must be initialized"

        # Handle .docsible metadata file
        docsible_path = role_path / ".docsible"
        if not no_docsible:
            manage_docsible_file_keys(docsible_path)

        # Get meta file
        meta_path = self.project_structure.get_meta_file(role_path)
        if meta_path is None:
            logger.warning(f"No meta file found for role {role_path.name}")
            meta_path = role_path / "meta" / "main.yml"

        return {
            "meta": load_yaml_generic(meta_path) if meta_path.exists() else {},
            "docsible": load_yaml_generic(docsible_path) if not no_docsible else None,
        }

    def _build_vars_info(self, role_path: Path) -> dict:
        """Extract defaults and vars.

        Args:
            role_path: Path to role directory

        Returns:
            Dictionary with 'defaults' and 'vars' keys
        """
        assert self.project_structure is not None, "project_structure must be initialized"

        defaults_dir = self.project_structure.get_defaults_dir(role_path)
        vars_dir = self.project_structure.get_vars_dir(role_path)

        return {
            "defaults": load_yaml_files_from_dir_custom(defaults_dir) or [],
            "vars": load_yaml_files_from_dir_custom(vars_dir) or [],
        }

    def _build_tasks_info(self, role_path: Path, processing: ProcessingConfig) -> dict:
        """Extract and process tasks.

        Args:
            role_path: Path to role directory
            processing: Processing configuration

        Returns:
            Dictionary with 'tasks' key containing list of task file info
        """
        assert self.project_structure is not None, "project_structure must be initialized"

        tasks_dir = self.project_structure.get_tasks_dir(role_path)
        tasks_list: list[dict[str, Any]] = []

        if not (tasks_dir.exists() and tasks_dir.is_dir()):
            return {"tasks": tasks_list}

        yaml_extensions = self.project_structure.get_yaml_extensions()

        for dirpath, _, filenames in os.walk(str(tasks_dir)):
            for task_file in filenames:
                if not any(task_file.endswith(ext) for ext in yaml_extensions):
                    continue

                file_path = Path(dirpath) / task_file
                tasks_data = load_yaml_generic(file_path)

                if not tasks_data:
                    continue

                relative_path = file_path.relative_to(tasks_dir)
                task_info: dict[str, Any] = {
                    "file": str(relative_path),
                    "tasks": [],
                    "mermaid": [],
                    "comments": [],
                    "lines": [],
                    "line_ranges": [],
                }

                # Extract optional metadata
                if processing.comments:
                    task_info["comments"] = get_task_comments(str(file_path))
                if processing.task_line:
                    task_info["lines"] = get_task_line_numbers(str(file_path))

                # Always extract line ranges (lightweight operation for phase detection)
                try:
                    task_info["line_ranges"] = get_task_line_ranges(str(file_path))
                except Exception as e:
                    logger.debug(f"Could not extract line ranges for {file_path}: {e}")

                # Process tasks
                if isinstance(tasks_data, list):
                    for task in tasks_data:
                        if isinstance(task, dict) and task:
                            processed_tasks = process_special_task_keys(task)
                            task_info["tasks"].extend(processed_tasks)
                            task_info["mermaid"].append(task)

                    tasks_list.append(task_info)

        return {"tasks": tasks_list}

    def _build_handlers_info(self, role_path: Path) -> dict:
        """Extract handlers.

        Args:
            role_path: Path to role directory

        Returns:
            Dictionary with 'handlers' key containing list of handler info
        """
        assert self.project_structure is not None, "project_structure must be initialized"

        handlers_dir = role_path / "handlers"
        handlers_list: list[dict[str, Any]] = []

        if not (handlers_dir.exists() and handlers_dir.is_dir()):
            return {"handlers": handlers_list}

        yaml_extensions = self.project_structure.get_yaml_extensions()

        for dirpath, _, filenames in os.walk(str(handlers_dir)):
            for handler_file in filenames:
                if not any(handler_file.endswith(ext) for ext in yaml_extensions):
                    continue

                file_path = Path(dirpath) / handler_file
                handlers_data = load_yaml_generic(file_path)

                if not (handlers_data and isinstance(handlers_data, list)):
                    continue

                for handler in handlers_data:
                    if not (isinstance(handler, dict) and "name" in handler):
                        continue

                    # Find the module (first key that's not a standard ansible key)
                    excluded_keys = ["name", "notify", "when", "tags", "listen"]
                    module = next(
                        (k for k in handler.keys() if k not in excluded_keys),
                        "unknown",
                    )

                    handler_info = {
                        "name": handler.get("name", "Unnamed handler"),
                        "module": module,
                        "listen": handler.get("listen", []),
                        "file": str(Path(file_path).relative_to(handlers_dir)),
                    }
                    handlers_list.append(handler_info)

        return {"handlers": handlers_list}

    def _build_playbook_info(
        self, playbook_content: str | None, role_name: str, generate_graph: bool
    ) -> dict:
        """Build playbook information including dependencies.

        Args:
            playbook_content: Playbook YAML content
            role_name: Current role name
            generate_graph: Whether to generate Mermaid graph

        Returns:
            Dictionary with 'playbook' key containing content, graph, dependencies
        """
        if not playbook_content:
            return {
                "playbook": {
                    "content": None,
                    "graph": None,
                    "dependencies": [],
                }
            }

        # Generate playbook graph if requested
        graph = None
        if generate_graph:
            try:
                playbook_data = yaml.safe_load(playbook_content)
                graph = generate_mermaid_playbook(playbook_data)
            except Exception as e:
                logger.warning(f"Could not generate playbook graph: {e}")

        # Extract role dependencies from playbook
        dependencies = self._extract_playbook_dependencies(playbook_content, role_name)

        return {
            "playbook": {
                "content": playbook_content,
                "graph": graph,
                "dependencies": dependencies,
            }
        }

    def _extract_playbook_dependencies(
        self, playbook_content: str, current_role_name: str
    ) -> list[str]:
        """Extract role dependencies from playbook content.

        Searches for roles in:
        - roles: section
        - include_role/import_role tasks in pre_tasks, tasks, post_tasks

        Args:
            playbook_content: YAML content of playbook
            current_role_name: Name of current role (to exclude from dependencies)

        Returns:
            Sorted list of role names (excluding current role)
        """
        try:
            playbook = yaml.safe_load(playbook_content)
            if not isinstance(playbook, list):
                return []

            role_names = set()

            for play in playbook:
                if not isinstance(play, dict):
                    continue

                # Extract from roles: section
                roles = play.get("roles", [])
                for role in roles:
                    role_name = self._extract_role_name(role)
                    if role_name and role_name != current_role_name:
                        role_names.add(role_name)

                # Extract from task sections
                for section in ["pre_tasks", "tasks", "post_tasks"]:
                    tasks = play.get(section, [])
                    if not isinstance(tasks, list):
                        continue

                    for task in tasks:
                        if not isinstance(task, dict):
                            continue

                        for action in ["include_role", "import_role"]:
                            if action in task:
                                role_name = self._extract_role_name(task[action])
                                if role_name and role_name != current_role_name:
                                    role_names.add(role_name)

            return sorted(list(role_names))

        except Exception as e:
            logger.warning(f"Could not extract playbook dependencies: {e}")
            return []

    def _extract_role_name(self, role_spec: Any) -> str | None:
        """Extract role name from various role specification formats.

        Args:
            role_spec: Role specification (string, dict, or other)

        Returns:
            Role name or None if cannot be extracted
        """
        if isinstance(role_spec, str):
            return role_spec
        elif isinstance(role_spec, dict):
            return str(role_spec.get("role") or role_spec.get("name") or "")
        return None

    def _build_repository_info(
        self, role_path: Path, repository: RepositoryConfig
    ) -> dict:
        """Build repository information.

        Args:
            role_path: Path to role directory
            repository: Repository configuration

        Returns:
            Dictionary with repository_url, repository_type, repository_branch
        """
        repo_url = repository.repository_url
        repo_type = repository.repo_type
        repo_branch = repository.repo_branch

        # Auto-detect if requested
        if repo_url == "detect":
            try:
                git_info = get_repo_info(str(role_path)) or {}
                repo_url = git_info.get("repository")
                repo_branch = repo_branch or git_info.get("branch", "main")
                repo_type = repo_type or git_info.get("repository_type")
            except Exception as e:
                logger.warning(f"Could not get Git info: {e}")
                repo_url = None

        return {
            "repository": repo_url,
            "repository_type": repo_type,
            "repository_branch": repo_branch,
        }

    def _get_argument_specs(self, role_path: Path) -> dict | None:
        """Get argument specifications if available.

        Args:
            role_path: Path to role directory

        Returns:
            Argument specs dictionary or None
        """
        assert self.project_structure is not None, "project_structure must be initialized"

        argument_specs_path = self.project_structure.get_argument_specs_file(role_path)
        if argument_specs_path and argument_specs_path.exists():
            return load_yaml_generic(argument_specs_path)
        return None
