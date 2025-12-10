"""Project type detection for Ansible projects."""
import os
from pathlib import Path
from typing import List, Dict, Any


def detect_project_type(root_path: Path, defaults: Dict[str, Any]) -> str:
    """Auto-detect the project type based on directory structure.

    Args:
        root_path: Root directory of the project
        defaults: Default configuration dictionary

    Returns:
        Project type: 'collection', 'awx', 'monorepo', 'multi-role', 'role', or 'unknown'
    """
    # Check for collection marker (galaxy.yml/yaml)
    for marker in defaults["collection_marker_files"]:
        if (root_path / marker).exists():
            return "collection"

    # Check for AWX project structure
    if is_awx_project(root_path):
        return "awx"

    # Check for monorepo (multiple roles at different levels)
    if is_monorepo(root_path):
        return "monorepo"

    # Check for regular multi-role repo (just roles/ at root, no galaxy.yml)
    if (root_path / "roles").is_dir():
        return "multi-role"

    # Check for standard role
    if is_standard_role(root_path):
        return "role"

    return "unknown"


def is_awx_project(root_path: Path) -> bool:
    """Detect AWX project structure.

    Args:
        root_path: Root directory of the project

    Returns:
        True if project has both roles/ and inventory/inventories/ directories
    """
    # AWX projects must have BOTH:
    # - roles/ directory
    # - inventory/ or inventories/ directory
    has_roles = (root_path / "roles").is_dir()
    has_inventory = (root_path / "inventory").exists() or (
        root_path / "inventories"
    ).exists()

    return has_roles and has_inventory


def is_monorepo(root_path: Path) -> bool:
    """Detect monorepo structure (e.g., ansible/roles/, projects/ansible/).

    Args:
        root_path: Root directory of the project

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
        if (root_path / pattern).is_dir():
            return True

    return False


def is_standard_role(root_path: Path) -> bool:
    """Detect standard Ansible role structure.

    Args:
        root_path: Root directory of the project

    Returns:
        True if directory has at least one of: tasks/, defaults/, vars/, meta/
    """
    # A standard role has at least one of: tasks/, defaults/, vars/, meta/
    role_indicators = [
        (root_path / "tasks").is_dir(),
        (root_path / "defaults").is_dir(),
        (root_path / "vars").is_dir(),
        (root_path / "meta").is_dir(),
    ]
    return any(role_indicators)


def is_valid_role(path: Path) -> bool:
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


def find_collection_markers(root_path: Path, defaults: Dict[str, Any], search_path: Path = None) -> List[Path]:
    """Find all collection marker files (galaxy.yml/yaml) in the directory tree.

    Useful for detecting multiple collections in a monorepo.

    Args:
        root_path: Root directory of the project
        defaults: Default configuration dictionary
        search_path: Directory to search (default: project root)

    Returns:
        List of paths to galaxy.yml/yaml files
    """
    search = search_path or root_path
    markers = []

    for root, dirs, files in os.walk(search):
        for marker_file in defaults["collection_marker_files"]:
            if marker_file in files:
                markers.append(Path(root) / marker_file)

    return markers


def find_roles(root_path: Path, project_type: str, get_roles_dir_func) -> List[Path]:
    """Find all role directories in the project.

    Args:
        root_path: Root directory of the project
        project_type: Detected project type
        get_roles_dir_func: Function to get roles directory

    Returns:
        List of Path objects pointing to role directories
    """
    roles = []

    if project_type == "collection":
        # For collections, roles are in the roles/ directory
        roles_dir = get_roles_dir_func()
        if roles_dir.exists():
            for item in roles_dir.iterdir():
                if item.is_dir() and is_valid_role(item):
                    roles.append(item)

    elif project_type == "monorepo":
        # For monorepos, scan for roles in the configured/detected roles directory
        roles_dir = get_roles_dir_func()
        if roles_dir.exists():
            for item in roles_dir.iterdir():
                if item.is_dir() and is_valid_role(item):
                    roles.append(item)

    elif project_type == "awx":
        # For AWX, roles are typically in roles/ at root
        roles_dir = root_path / "roles"
        if roles_dir.exists():
            for item in roles_dir.iterdir():
                if item.is_dir() and is_valid_role(item):
                    roles.append(item)

    elif project_type == "multi-role":
        # For multi-role repos, roles are in roles/ at root (like collections, but no galaxy.yml)
        roles_dir = root_path / "roles"
        if roles_dir.exists():
            for item in roles_dir.iterdir():
                if item.is_dir() and is_valid_role(item):
                    roles.append(item)

    elif project_type == "role":
        # Single role - return the root path itself
        roles.append(root_path)

    return roles
