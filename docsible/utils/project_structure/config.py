"""Configuration loading and example generation."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


def load_config(root_path: Path) -> Dict[str, Any]:
    """Load configuration from .docsible.yml if it exists.

    Args:
        root_path: Root directory of the project

    Returns:
        Configuration dictionary from 'structure' key, or empty dict if not found
    """
    config_paths = [
        root_path / ".docsible.yml",
        root_path / ".docsible.yaml",
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
