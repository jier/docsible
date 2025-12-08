"""Module for handling flexible Ansible project structures.

Supports standard roles, collections, AWX projects, and monorepos.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from docsible import constants

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

    def __init__(self, root_path: str, config: Optional[Dict[str, Any]] = None):
        """Initialize ProjectStructure with a root path and optional configuration.

        Args:
            root_path: Root directory of the project
            config: Optional configuration dict (overrides loaded config)
        """
        self.root_path = Path(root_path).resolve()
        self.config = config or self._load_config()
        self.project_type = self._detect_project_type()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from .docsible.yml if it exists.

        Returns:
            Configuration dictionary from 'structure' key, or empty dict if not found
        """
        config_paths = [
            self.root_path / ".docsible.yml",
            self.root_path / ".docsible.yaml",
        ]

        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        loaded_config = yaml.safe_load(f) or {}
                    logger.info(f"Loaded configuration from {config_path}")
                    return loaded_config.get("structure", {})
                except Exception as e:
                    logger.warning(f"Error loading config from {config_path}: {e}")

        return {}

    def _detect_project_type(self) -> str:
        """Auto-detect the project type based on directory structure.

        Returns:
            Project type: 'collection', 'awx', 'monorepo', 'multi-role', 'role', or 'unknown'
        """
        # Check for collection marker (galaxy.yml/yaml)
        for marker in self.DEFAULTS["collection_marker_files"]:
            if (self.root_path / marker).exists():
                return "collection"

        # Check for AWX project structure
        if self._is_awx_project():
            return "awx"

        # Check for monorepo (multiple roles at different levels)
        if self._is_monorepo():
            return "monorepo"

        # Check for regular multi-role repo (just roles/ at root, no galaxy.yml)
        if (self.root_path / "roles").is_dir():
            return "multi-role"

        # Check for standard role
        if self._is_standard_role():
            return "role"

        return "unknown"

    def _is_awx_project(self) -> bool:
        """Detect AWX project structure.

        Returns:
            True if project has both roles/ and inventory/inventories/ directories
        """
        # AWX projects must have BOTH:
        # - roles/ directory
        # - inventory/ or inventories/ directory
        has_roles = (self.root_path / "roles").is_dir()
        has_inventory = (self.root_path / "inventory").exists() or (
            self.root_path / "inventories"
        ).exists()

        return has_roles and has_inventory

    def _is_monorepo(self) -> bool:
        """Detect monorepo structure (e.g., ansible/roles/, projects/ansible/).

        Returns:
            True if roles directory exists at non-root nested path
        """
        # Look for roles directory not at root level
        monorepo_patterns = [
            "ansible/roles",
            "playbooks/roles",
            "automation/roles",
        ]

        for pattern in monorepo_patterns:
            if (self.root_path / pattern).is_dir():
                return True

        return False

    def _is_standard_role(self) -> bool:
        """Detect standard Ansible role structure.

        Returns:
            True if directory has at least one of: tasks/, defaults/, vars/, meta/
        """
        # A standard role has at least one of: tasks/, defaults/, vars/, meta/
        role_indicators = [
            (self.root_path / "tasks").is_dir(),
            (self.root_path / "defaults").is_dir(),
            (self.root_path / "vars").is_dir(),
            (self.root_path / "meta").is_dir(),
        ]
        return any(role_indicators)

    def _resolve_path(
        self, key: str, base_path: Optional[Path] = None, default: Optional[str] = None
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

        # Check config first
        if key in self.config:
            return base / self.config[key]

        # Use default
        if default is None:
            default = self.DEFAULTS.get(key, key)

        return base / default

    def get_defaults_dir(self, role_path: Optional[Path] = None) -> Path:
        """Get the defaults directory for a role."""
        return self._resolve_path("defaults_dir", role_path or self.root_path)

    def get_vars_dir(self, role_path: Optional[Path] = None) -> Path:
        """Get the vars directory for a role."""
        return self._resolve_path("vars_dir", role_path or self.root_path)

    def get_tasks_dir(self, role_path: Optional[Path] = None) -> Path:
        """Get the tasks directory for a role."""
        return self._resolve_path("tasks_dir", role_path or self.root_path)
    
    def get_library_dir(self, role_path: Optional[Path] = None) -> Path:
        """Get the library directory for a role (custom modules)."""
        return self._resolve_path("library_dir", role_path or self.root_path)

    def get_lookup_plugins_dir(self, role_path: Optional[Path] = None) -> Path:
        """Get the lookup_plugins directory for a role."""
        return self._resolve_path("lookup_plugins_dir", role_path or self.root_path)

    def get_templates_dir(self, role_path: Optional[Path] = None) -> Path:
        """Get the templates directory for a role."""
        return self._resolve_path("templates_dir", role_path or self.root_path)
    
    def get_meta_dir(self, role_path: Optional[Path] = None) -> Path:
        """Get the meta directory for a role."""
        return self._resolve_path("meta_dir", role_path or self.root_path)

    def get_meta_file(self, role_path: Optional[Path] = None) -> Optional[Path]:
        """
        Get the meta/main.yml or meta/main.yaml file for a role.
        Returns None if not found.
        """
        meta_dir = self.get_meta_dir(role_path)
        meta_filename = self.config.get("meta_file", self.DEFAULTS["meta_file"])

        for ext in self.DEFAULTS["yaml_extensions"]:
            meta_path = meta_dir / f"{meta_filename}{ext}"
            if meta_path.exists():
                return meta_path

        return None

    def get_argument_specs_file(
        self, role_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Get the meta/argument_specs.yml or .yaml file for a role.
        Returns None if not found.
        """
        meta_dir = self.get_meta_dir(role_path)
        specs_filename = self.config.get(
            "argument_specs_file", self.DEFAULTS["argument_specs_file"]
        )

        for ext in self.DEFAULTS["yaml_extensions"]:
            specs_path = meta_dir / f"{specs_filename}{ext}"
            if specs_path.exists():
                return specs_path

        return None

    def get_roles_dir(self, collection_path: Optional[Path] = None) -> Path:
        """Get the roles directory for a collection or monorepo."""
        base = collection_path or self.root_path

        # Check config first
        if "roles_dir" in self.config:
            return base / self.config["roles_dir"]

        # Auto-detect for monorepo
        if self.project_type == "monorepo":
            monorepo_patterns = [
                "ansible/roles",
                "playbooks/roles",
                "automation/roles",
                "roles",  # Fallback
            ]

            for pattern in monorepo_patterns:
                roles_path = base / pattern
                if roles_path.is_dir():
                    return roles_path

        # Default
        return base / self.DEFAULTS["roles_dir"]

    def find_collection_markers(self, search_path: Optional[Path] = None) -> List[Path]:
        """Find all collection marker files (galaxy.yml/yaml) in the directory tree.

        Useful for detecting multiple collections in a monorepo.

        Args:
            search_path: Directory to search (default: project root)

        Returns:
            List of paths to galaxy.yml/yaml files
        """
        search = search_path or self.root_path
        markers = []

        for root, dirs, files in os.walk(search):
            for marker_file in self.DEFAULTS["collection_marker_files"]:
                if marker_file in files:
                    markers.append(Path(root) / marker_file)

        return markers

    def find_roles(self, search_path: Optional[Path] = None) -> List[Path]:
        """Find all role directories in the project.

        Args:
            search_path: Optional search path (currently unused, reserved for future use)

        Returns:
            List of Path objects pointing to role directories
        """
        roles = []

        if self.project_type == "collection":
            # For collections, roles are in the roles/ directory
            roles_dir = self.get_roles_dir()
            if roles_dir.exists():
                for item in roles_dir.iterdir():
                    if item.is_dir() and self._is_valid_role(item):
                        roles.append(item)

        elif self.project_type == "monorepo":
            # For monorepos, scan for roles in the configured/detected roles directory
            roles_dir = self.get_roles_dir()
            if roles_dir.exists():
                for item in roles_dir.iterdir():
                    if item.is_dir() and self._is_valid_role(item):
                        roles.append(item)

        elif self.project_type == "awx":
            # For AWX, roles are typically in roles/ at root
            roles_dir = self.root_path / "roles"
            if roles_dir.exists():
                for item in roles_dir.iterdir():
                    if item.is_dir() and self._is_valid_role(item):
                        roles.append(item)

        elif self.project_type == "multi-role":
            # For multi-role repos, roles are in roles/ at root (like collections, but no galaxy.yml)
            roles_dir = self.root_path / "roles"
            if roles_dir.exists():
                for item in roles_dir.iterdir():
                    if item.is_dir() and self._is_valid_role(item):
                        roles.append(item)

        elif self.project_type == "role":
            # Single role - return the root path itself
            roles.append(self.root_path)

        return roles

    def _is_valid_role(self, path: Path) -> bool:
        """Check if a directory is a valid Ansible role.

        Args:
            path: Directory path to check

        Returns:
            True if directory has at least one of: tasks/, defaults/, vars/, meta/
        """
        role_indicators = [
            (path / "tasks").is_dir(),
            (path / "defaults").is_dir(),
            (path / "vars").is_dir(),
            (path / "meta").is_dir(),
        ]
        return any(role_indicators)

    def get_test_playbook(self, role_path: Optional[Path] = None) -> Optional[Path]:
        """Get the test playbook path for a role.

        Args:
            role_path: Role directory path (default: project root)

        Returns:
            Path to test playbook, or None if not found
        """
        base = role_path or self.root_path
        playbook_path = self.config.get("test_playbook", self.DEFAULTS["test_playbook"])

        full_path = base / playbook_path
        return full_path if full_path.exists() else None

    def get_yaml_extensions(self) -> List[str]:
        """Get list of supported YAML file extensions.

        Returns:
            List of YAML extensions (e.g., ['.yml', '.yaml'])
        """
        return self.config.get("yaml_extensions", self.DEFAULTS["yaml_extensions"])

    def to_dict(self) -> Dict[str, Any]:
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


def create_example_config() -> str:
    """Generate an example .docsible.yml configuration file content.

    Returns:
        Example YAML configuration as string
    """
    example = """# Docsible Project Structure Configuration
# This file allows you to customize how docsible interprets your Ansible project structure.
# All paths are relative to the location of this file.
#
# Priority: CLI flags > .docsible.yml > Auto-detection > Built-in defaults

structure:
  # Directory names (without leading/trailing slashes)
  # Uncomment and modify only what you need to override

  defaults_dir: 'defaults'           # Where default variables are stored
  vars_dir: 'vars'                   # Where role variables are stored
  tasks_dir: 'tasks'                 # Where task files are located
  meta_dir: 'meta'                   # Where role metadata is stored
  roles_dir: 'roles'                 # Where roles are located (for collections/monorepos)
  handlers_dir: 'handlers'          # Where handlers are located (for collections/monorepos)
  templates_dir: 'templates'         # Where Jinja2 templates are located
  
  # Custom modules and plugins
  library_dir: 'library'                     # Custom Ansible modules
  lookup_plugins_dir: 'lookup_plugins'       # Custom lookup plugins 
  # For monorepo structures, you can specify nested paths:
  # roles_dir: 'ansible/roles'         # Example: monorepo with ansible subdirectory
  # roles_dir: 'playbooks/roles'       # Example: playbooks subdirectory

  # File names (without extensions - both .yml and .yaml are checked automatically)
  # meta_file: 'main'                  # Meta file name (meta/main.yml)
  # argument_specs_file: 'argument_specs'  # Argument specs file name

  # Test playbook path
  # test_playbook: 'tests/test.yml'    # Default test playbook location

  # Advanced: YAML file extensions to recognize
  yaml_extensions: ['.yml', '.yaml'] # File extensions to scan

# Examples for different project types:

# AWX Project:
# structure:
#   roles_dir: 'roles'

# Monorepo:
# structure:
#   roles_dir: 'ansible/roles'

# Custom directory names:
# structure:
#   defaults_dir: 'role_defaults'
#   vars_dir: 'variables'
#   tasks_dir: 'playbooks'
"""
    return example
