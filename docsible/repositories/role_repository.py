"""Repository for loading Ansible roles from the filesystem.

This module implements the Repository pattern for role data access,
providing a clean separation between file I/O operations and business logic.
"""

import logging
from pathlib import Path
from typing import cast

from docsible.models.role import Role
from docsible.utils.cache import cache_by_file_mtime
from docsible.utils.project_structure import ProjectStructure
from docsible.utils.special_tasks_keys import process_special_task_keys
from docsible.utils.yaml import (
    get_task_comments,
    get_task_line_numbers,
    load_yaml_files_from_dir_custom,
    load_yaml_generic,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Cached YAML Loading Functions
# ============================================================================

@cache_by_file_mtime
def _load_yaml_file_cached(path: Path) -> dict | list | None:
    """Load and parse a single YAML file with caching.

    Caches results by file path + modification time. Automatically invalidates
    when file changes.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML content (dict, list, or None)
    """
    return load_yaml_generic(path)


def _load_yaml_dir_cached(dir_path: Path) -> list[dict]:
    """Load all YAML files from directory with per-file caching.

    Uses cached loading for each individual file in the directory.

    Args:
        dir_path: Path to directory containing YAML files

    Returns:
        List of parsed YAML dictionaries
    """
    if not dir_path.exists() or not dir_path.is_dir():
        return []

    yaml_files = [
        f for f in dir_path.iterdir()
        if f.is_file() and f.suffix in ('.yml', '.yaml')
    ]

    results: list[dict] = []
    for yaml_file in yaml_files:
        content = _load_yaml_file_cached(yaml_file)
        if content and isinstance(content, dict):
            results.append(content)

    return results


class RoleRepository:
    """Repository for loading and saving Ansible role data from/to filesystem.

    This class encapsulates all file system operations related to roles,
    providing a clean interface for role data access.

    Attributes:
        project_structure: ProjectStructure instance for path resolution
    """

    def __init__(self, project_structure: ProjectStructure | None = None):
        """Initialize RoleRepository.

        Args:
            project_structure: ProjectStructure instance (created if None)
        """
        self.structure = project_structure

    def load(
        self,
        path: Path,
        include_comments: bool = False,
        include_line_numbers: bool = False,
    ) -> Role | None:
        """Load a role from filesystem path.

        Args:
            path: Path to role directory
            include_comments: Include task comments in loaded data
            include_line_numbers: Include task line numbers in loaded data

        Returns:
            Role instance or None if loading fails

        Example:
            >>> repo = RoleRepository()
            >>> role = repo.load(Path("/path/to/role"))
            >>> if role:
            ...     print(f"Loaded role: {role.name}")
        """
        try:
            if self.structure is None:
                self.structure = ProjectStructure(str(path))

            role_name = path.name

            # Load all role components
            defaults = self._load_defaults(path)
            vars_data = self._load_vars(path)
            tasks = self._load_tasks(path, include_comments, include_line_numbers)
            handlers = self._load_handlers(path)
            meta = self._load_meta(path)

            # Create Role instance
            role_dict = {
                "name": role_name,
                "path": path,
                "defaults": defaults,
                "vars": vars_data,
                "tasks": tasks,
                "handlers": handlers,
                "meta": meta or {},
            }

            return cast(Role, Role.model_validate(role_dict))

        except Exception as e:
            logger.error(f"Failed to load role from {path}: {e}")
            return None

    def _load_defaults(self, role_path: Path) -> list[dict]:
        """Load role defaults directory with caching.

        Uses per-file caching to avoid re-parsing unchanged YAML files.

        Args:
            role_path: Path to role directory

        Returns:
            List of default variable dictionaries
        """
        assert self.structure is not None, "ProjectStructure must be initialized"
        defaults_dir = self.structure.get_defaults_dir(role_path)
        if not defaults_dir.exists():
            logger.debug(f"No defaults directory found in {role_path}")
            return []

        # Use cached loading
        defaults_data = _load_yaml_dir_cached(defaults_dir)
        return defaults_data or []

    def _load_vars(self, role_path: Path) -> list[dict]:
        """Load role vars directory with caching.

        Uses per-file caching to avoid re-parsing unchanged YAML files.

        Args:
            role_path: Path to role directory

        Returns:
            List of variable dictionaries
        """
        assert self.structure is not None, "ProjectStructure must be initialized"
        vars_dir = self.structure.get_vars_dir(role_path)
        if not vars_dir.exists():
            logger.debug(f"No vars directory found in {role_path}")
            return []

        # Use cached loading
        vars_data = _load_yaml_dir_cached(vars_dir)
        return vars_data or []

    def _load_tasks(
        self,
        role_path: Path,
        include_comments: bool = False,
        include_line_numbers: bool = False,
    ) -> list[dict]:
        """Load role tasks directory with caching.

        Uses per-file caching to avoid re-parsing unchanged YAML files.
        This is the most critical caching point as roles can have 10-50+ task files.

        Args:
            role_path: Path to role directory
            include_comments: Include task comments
            include_line_numbers: Include line numbers

        Returns:
            List of task file dictionaries
        """
        assert self.structure is not None, "ProjectStructure must be initialized"
        tasks_dir = self.structure.get_tasks_dir(role_path)
        if not tasks_dir.exists() or not tasks_dir.is_dir():
            logger.debug(f"No tasks directory found in {role_path}")
            return []

        tasks_list = []
        yaml_extensions = self.structure.get_yaml_extensions()

        import os
        for dirpath, _ , filenames in os.walk(str(tasks_dir)):
            for task_file in filenames:
                if any(task_file.endswith(ext) for ext in yaml_extensions):
                    file_path = os.path.join(dirpath, task_file)
                    # Use cached loading for each task file
                    tasks_data = _load_yaml_file_cached(Path(file_path))

                    if tasks_data:
                        relative_path = os.path.relpath(file_path, str(tasks_dir))
                        from typing import Any
                        task_info: dict[str, Any] = {
                            "file": relative_path,
                            "tasks": [],
                            "mermaid": [],
                            "comments": [],
                            "lines": [],
                        }

                        # Get comments and line numbers if requested
                        if include_comments:
                            task_info["comments"] = get_task_comments(file_path)
                        if include_line_numbers:
                            task_info["lines"] = get_task_line_numbers(file_path)

                        # Process tasks
                        if isinstance(tasks_data, list):
                            for task in tasks_data:
                                if isinstance(task, dict) and len(task.keys()) > 0:
                                    processed_tasks = process_special_task_keys(task)
                                    task_info["tasks"].extend(processed_tasks)
                                    task_info["mermaid"].append(task)

                        tasks_list.append(task_info)

        return tasks_list

    def _load_handlers(self, role_path: Path) -> list[dict]:
        """Load role handlers directory with caching.

        Uses per-file caching to avoid re-parsing unchanged YAML files.

        Args:
            role_path: Path to role directory

        Returns:
            List of handler dictionaries
        """
        assert self.structure is not None, "ProjectStructure must be initialized"
        handlers_dir = role_path / "handlers"
        if not handlers_dir.exists() or not handlers_dir.is_dir():
            logger.debug(f"No handlers directory found in {role_path}")
            return []

        handlers_list: list[dict] = []
        yaml_extensions = self.structure.get_yaml_extensions()

        import os

        for dirpath, _ , filenames in os.walk(str(handlers_dir)):
            for handler_file in filenames:
                if any(handler_file.endswith(ext) for ext in yaml_extensions):
                    file_path = os.path.join(dirpath, handler_file)
                    # Use cached loading for each handler file
                    handlers_data = _load_yaml_file_cached(Path(file_path))

                    if handlers_data and isinstance(handlers_data, list):
                        for handler in handlers_data:
                            if isinstance(handler, dict) and "name" in handler:
                                # Extract handler info
                                handler_info = {
                                    "name": handler.get("name", "Unnamed handler"),
                                    "module": next(
                                        (
                                            k
                                            for k in handler.keys()
                                            if k
                                            not in [
                                                "name",
                                                "notify",
                                                "when",
                                                "tags",
                                                "listen",
                                            ]
                                        ),
                                        "unknown",
                                    ),
                                    "listen": handler.get("listen", []),
                                    "file": os.path.relpath(
                                        file_path, str(handlers_dir)
                                    ),
                                }
                                handlers_list.append(handler_info)

        return handlers_list

    def _load_meta(self, role_path: Path) -> dict | None:
        """Load role metadata from meta/main.yml with caching.

        Uses file-based caching to avoid re-parsing unchanged metadata files.

        Args:
            role_path: Path to role directory

        Returns:
            Metadata dictionary or None if not found
        """
        assert self.structure is not None, "ProjectStructure must be initialized"
        meta_path = self.structure.get_meta_file(role_path)
        if meta_path is None or not meta_path.exists():
            logger.debug(f"No meta file found in {role_path}")
            return None

        # Use cached loading
        meta_data = _load_yaml_file_cached(meta_path)
        if meta_data and isinstance(meta_data, dict):
            return meta_data
        return None

    def exists(self, path: Path) -> bool:
        """Check if a role exists at the given path.

        Args:
            path: Path to check

        Returns:
            True if path exists and is a directory

        Example:
            >>> repo = RoleRepository()
            >>> if repo.exists(Path("/path/to/role")):
            ...     role = repo.load(Path("/path/to/role"))
        """
        return path.exists() and path.is_dir()

    def get_role_names_in_collection(self, collection_path: Path) -> list[str]:
        """Get list of role names in a collection.

        Args:
            collection_path: Path to collection directory

        Returns:
            List of role names found in the collection

        Example:
            >>> repo = RoleRepository()
            >>> roles = repo.get_role_names_in_collection(Path("/path/to/collection"))
            >>> print(f"Found {len(roles)} roles")
        """
        if self.structure is None:
            self.structure = ProjectStructure(str(collection_path))

        roles_dir = self.structure.get_roles_dir()
        if not roles_dir.exists() or not roles_dir.is_dir():
            logger.debug(f"No roles directory found in {collection_path}")
            return []

        import os

        role_names = []
        for item in os.listdir(str(roles_dir)):
            role_path = roles_dir / item
            if role_path.is_dir():
                role_names.append(item)

        return role_names
