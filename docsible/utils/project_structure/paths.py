"""Path resolution utilities for Ansible project structures."""

from pathlib import Path
from typing import Any


def resolve_path(
    key: str,
    config: dict[str, str| Path],
    defaults: dict[str, Any],
    base_path: Path,
    default: str | None = None,
) -> Path:
    """
    Resolve a path using priority: config > auto-detect > default.

    Args:
        key: Configuration key (e.g., 'defaults_dir')
        config: Configuration dictionary
        defaults: Default configuration dictionary
        base_path: Base path to resolve relative paths from
        default: Default value if not in config

    Returns:
        Resolved Path object
    """
    # Check config first
    if key in config:
        return base_path / config[key]

    # Use default
    if default is None:
        default = defaults.get(key, key)

    return base_path / str(default)


def get_defaults_dir(
    root_path: Path,
    config: dict[str, Any],
    defaults: dict[str, Any],
    role_path: Path | None = None,
) -> Path:
    """Get the defaults directory for a role."""
    return resolve_path("defaults_dir", config, defaults, role_path or root_path)


def get_vars_dir(
    root_path: Path,
    config: dict[str, Any],
    defaults: dict[str, Any],
    role_path: Path | None = None,
) -> Path:
    """Get the vars directory for a role."""
    return resolve_path("vars_dir", config, defaults, role_path or root_path)


def get_tasks_dir(
    root_path: Path,
    config: dict[str, Any],
    defaults: dict[str, Any],
    role_path: Path | None = None,
) -> Path:
    """Get the tasks directory for a role."""
    return resolve_path("tasks_dir", config, defaults, role_path or root_path)


def get_library_dir(
    root_path: Path,
    config: dict[str, Any],
    defaults: dict[str, Any],
    role_path: Path | None = None,
) -> Path:
    """Get the library directory for a role (custom modules)."""
    return resolve_path("library_dir", config, defaults, role_path or root_path)


def get_lookup_plugins_dir(
    root_path: Path,
    config: dict[str, Any],
    defaults: dict[str, Any],
    role_path: Path | None = None,
) -> Path:
    """Get the lookup_plugins directory for a role."""
    return resolve_path("lookup_plugins_dir", config, defaults, role_path or root_path)


def get_templates_dir(
    root_path: Path,
    config: dict[str, Any],
    defaults: dict[str, Any],
    role_path: Path | None = None,
) -> Path:
    """Get the templates directory for a role."""
    return resolve_path("templates_dir", config, defaults, role_path or root_path)


def get_meta_dir(
    root_path: Path,
    config: dict[str, Any],
    defaults: dict[str, Any],
    role_path: Path | None = None,
) -> Path:
    """Get the meta directory for a role."""
    return resolve_path("meta_dir", config, defaults, role_path or root_path)


def get_meta_file(
    root_path: Path,
    config: dict[str, Any],
    defaults: dict[str, Any],
    role_path: Path | None = None,
) -> Path | None:
    """
    Get the meta/main.yml or meta/main.yaml file for a role.
    Returns None if not found.
    """
    meta_dir = get_meta_dir(root_path, config, defaults, role_path)
    meta_filename = config.get("meta_file", defaults["meta_file"])

    for ext in defaults["yaml_extensions"]:
        meta_path = meta_dir / f"{meta_filename}{ext}"
        if meta_path.exists():
            return meta_path

    return None


def get_argument_specs_file(
    root_path: Path,
    config: dict[str, Any],
    defaults: dict[str, Any],
    role_path: Path | None = None,
) -> Path | None:
    """
    Get the meta/argument_specs.yml or .yaml file for a role.
    Returns None if not found.
    """
    meta_dir = get_meta_dir(root_path, config, defaults, role_path)
    specs_filename = config.get("argument_specs_file", defaults["argument_specs_file"])

    for ext in defaults["yaml_extensions"]:
        specs_path = meta_dir / f"{specs_filename}{ext}"
        if specs_path.exists():
            return specs_path

    return None


def get_roles_dir(
    root_path: Path,
    config: dict[str, Any],
    defaults: dict[str, Any],
    project_type: str,
    collection_path: Path | None = None,
) -> Path:
    """Get the roles directory for a collection or monorepo."""
    base = collection_path or root_path

    # Check config first
    if "roles_dir" in config:
        return base / str(config["roles_dir"])

    # Auto-detect for monorepo
    if project_type == "monorepo":
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
    return base / str(defaults["roles_dir"])


def get_test_playbook(
    root_path: Path,
    config: dict[str, Any],
    defaults: dict[str, Any],
    role_path: Path | None = None,
) -> Path | None:
    """Get the test playbook path for a role.

    Args:
        root_path: Root directory of the project
        config: Configuration dictionary
        defaults: Default configuration dictionary
        role_path: Role directory path (default: project root)

    Returns:
        Path to test playbook, or None if not found
    """
    base = role_path or root_path
    playbook_path = config.get("test_playbook", defaults["test_playbook"])

    full_path = base / playbook_path
    return full_path if full_path.exists() else None


def get_yaml_extensions(config: dict[str, Any], defaults: dict[str, Any]) -> list[str]:
    """Get list of supported YAML file extensions.

    Args:
        config: Configuration dictionary
        defaults: Default configuration dictionary

    Returns:
        List of YAML extensions (e.g., ['.yml', '.yaml'])
    """
    return config.get("yaml_extensions", defaults["yaml_extensions"])
