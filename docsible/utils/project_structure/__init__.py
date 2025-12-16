"""Module for handling flexible Ansible project structures.

Supports standard roles, collections, AWX projects, and monorepos.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from docsible import constants

from . import config as config_module
from . import detector, paths

logger = logging.getLogger(__name__)


class ProjectStructure:
    """Handles flexible Ansible project structure detection and path resolution.

    Supports configuration via .docsible.yml and auto-detection.
    Priority order: CLI overrides > .docsible.yml config > Auto-detection > Defaults

    Attributes:
        root_path: Root directory of the project
        config: Loaded configuration dictionary
        project_type: Detected project type (collection, awx, monorepo, etc.)
    """

    # Default directory and file patterns - use constants module
    DEFAULTS = {
        "defaults_dir": constants.DEFAULT_DEFAULTS_DIR,
        "vars_dir": constants.DEFAULT_VARS_DIR,
        "tasks_dir": constants.DEFAULT_TASKS_DIR,
        "meta_dir": constants.DEFAULT_META_DIR,
        "meta_file": constants.DEFAULT_META_FILE,
        "handlers_dir": constants.DEFAULT_HANDLERS_DIR,
        "library_dir": constants.DEFAULT_LIBRARY_DIR,
        "templates_dir": constants.DEFAULT_TEMPLATES_DIR,
        "lookup_plugins_dir": constants.DEFAULT_LOOKUP_PLUGINS_DIR,
        "argument_specs_file": constants.DEFAULT_ARGUMENT_SPECS_FILE,
        "roles_dir": constants.DEFAULT_ROLES_DIR,
        "collection_marker_files": constants.COLLECTION_MARKER_FILES,
        "role_marker_files": constants.ROLE_MARKER_FILES,
        "yaml_extensions": constants.YAML_EXTENSIONS,
        "test_playbook": constants.DEFAULT_TEST_PLAYBOOK,
    }

    def __init__(self, root_path: str, config: dict[str, Any] | None = None):
        """Initialize ProjectStructure with a root path and optional configuration.

        Args:
            root_path: Root directory of the project
            config: Optional configuration dict (overrides loaded config)
        """
        self.root_path = Path(root_path).resolve()
        self.config = config or self._load_config()
        self.project_type = self._detect_project_type()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from .docsible.yml if it exists.

        Returns:
            Configuration dictionary from 'structure' key, or empty dict if not found
        """
        return config_module.load_config(self.root_path)

    def _detect_project_type(self) -> str:
        """Auto-detect the project type based on directory structure.

        Returns:
            Project type: 'collection', 'awx', 'monorepo', 'multi-role', 'role', or 'unknown'
        """
        return detector.detect_project_type(self.root_path, self.DEFAULTS)

    def _is_awx_project(self) -> bool:
        """Detect AWX project structure.

        Returns:
            True if project has both roles/ and inventory/inventories/ directories
        """
        return detector.is_awx_project(self.root_path)

    def _is_monorepo(self) -> bool:
        """Detect monorepo structure (e.g., ansible/roles/, projects/ansible/).

        Returns:
            True if roles directory exists at non-root nested path
        """
        return detector.is_monorepo(self.root_path)

    def _is_standard_role(self) -> bool:
        """Detect standard Ansible role structure.

        Returns:
            True if directory has at least one of: tasks/, defaults/, vars/, meta/
        """
        return detector.is_standard_role(self.root_path)

    def _resolve_path(
        self, key: str, base_path: Path | None = None, default: str | None = None
    ) -> Path:
        """
        Resolve a path using priority: config > auto-detect > default.

        Args:
            key: Configuration key (e.g., 'defaults_dir')
            base_path: Base path to resolve relative paths from
            default: Default value if not in config

        Returns:
            Resolved Path object
        """
        base = base_path or self.root_path
        return paths.resolve_path(key, self.config, self.DEFAULTS, base, default)

    def get_defaults_dir(self, role_path: Path | None = None) -> Path:
        """Get the defaults directory for a role."""
        return paths.get_defaults_dir(
            self.root_path, self.config, self.DEFAULTS, role_path
        )

    def get_vars_dir(self, role_path: Path | None = None) -> Path:
        """Get the vars directory for a role."""
        return paths.get_vars_dir(self.root_path, self.config, self.DEFAULTS, role_path)

    def get_tasks_dir(self, role_path: Path | None = None) -> Path:
        """Get the tasks directory for a role."""
        return paths.get_tasks_dir(
            self.root_path, self.config, self.DEFAULTS, role_path
        )

    def get_library_dir(self, role_path: Path | None = None) -> Path:
        """Get the library directory for a role (custom modules)."""
        return paths.get_library_dir(
            self.root_path, self.config, self.DEFAULTS, role_path
        )

    def get_lookup_plugins_dir(self, role_path: Path | None = None) -> Path:
        """Get the lookup_plugins directory for a role."""
        return paths.get_lookup_plugins_dir(
            self.root_path, self.config, self.DEFAULTS, role_path
        )

    def get_templates_dir(self, role_path: Path | None = None) -> Path:
        """Get the templates directory for a role."""
        return paths.get_templates_dir(
            self.root_path, self.config, self.DEFAULTS, role_path
        )

    def get_meta_dir(self, role_path: Path | None = None) -> Path:
        """Get the meta directory for a role."""
        return paths.get_meta_dir(self.root_path, self.config, self.DEFAULTS, role_path)

    def get_meta_file(self, role_path: Path | None = None) -> Path | None:
        """
        Get the meta/main.yml or meta/main.yaml file for a role.
        Returns None if not found.
        """
        return paths.get_meta_file(
            self.root_path, self.config, self.DEFAULTS, role_path
        )

    def get_argument_specs_file(
        self, role_path: Path | None = None
    ) -> Path | None:
        """
        Get the meta/argument_specs.yml or .yaml file for a role.
        Returns None if not found.
        """
        return paths.get_argument_specs_file(
            self.root_path, self.config, self.DEFAULTS, role_path
        )

    def get_roles_dir(self, collection_path: Path | None = None) -> Path:
        """Get the roles directory for a collection or monorepo."""
        return paths.get_roles_dir(
            self.root_path,
            self.config,
            self.DEFAULTS,
            self.project_type,
            collection_path,
        )

    def find_collection_markers(self, search_path: Path | None = None) -> list[Path]:
        """Find all collection marker files (galaxy.yml/yaml) in the directory tree.

        Useful for detecting multiple collections in a monorepo.

        Args:
            search_path: Directory to search (default: project root)

        Returns:
            List of paths to galaxy.yml/yaml files
        """
        return detector.find_collection_markers(
            self.root_path, self.DEFAULTS, search_path
        )

    def find_roles(self, search_path: Path | None = None) -> list[Path]:
        """Find all role directories in the project.

        Args:
            search_path: Optional search path (currently unused, reserved for future use)

        Returns:
            List of Path objects pointing to role directories
        """
        return detector.find_roles(
            self.root_path, self.project_type, lambda: self.get_roles_dir()
        )

    def _is_valid_role(self, path: Path) -> bool:
        """Check if a directory is a valid Ansible role.

        Args:
            path: Directory path to check

        Returns:
            True if directory has at least one of: tasks/, defaults/, vars/, meta/
        """
        return detector.is_valid_role(path)

    def get_test_playbook(self, role_path: Path | None = None) -> Path | None:
        """Get the test playbook path for a role.

        Args:
            role_path: Role directory path (default: project root)

        Returns:
            Path to test playbook, or None if not found
        """
        return paths.get_test_playbook(
            self.root_path, self.config, self.DEFAULTS, role_path
        )

    def get_yaml_extensions(self) -> list[str]:
        """Get list of supported YAML file extensions.

        Returns:
            List of YAML extensions (e.g., ['.yml', '.yaml'])
        """
        return paths.get_yaml_extensions(self.config, self.DEFAULTS)

    def to_dict(self) -> dict[str, Any]:
        """Export the current configuration as a dictionary.

        Useful for debugging or generating .docsible.yml templates.

        Returns:
            Dictionary containing project type, paths, and configuration
        """
        return {
            "project_type": self.project_type,
            "root_path": str(self.root_path),
            "config": self.config,
            "detected_structure": {
                "defaults_dir": str(self.get_defaults_dir()),
                "vars_dir": str(self.get_vars_dir()),
                "tasks_dir": str(self.get_tasks_dir()),
                "meta_dir": str(self.get_meta_dir()),
                "roles_dir": str(self.get_roles_dir()),
            },
        }


# Re-export standalone function
def create_example_config() -> str:
    """Generate an example .docsible.yml configuration file content.

    Returns:
        Example YAML configuration as string
    """
    return config_module.create_example_config()


__all__ = ["ProjectStructure", "create_example_config"]
