"""Application-wide constants for Docsible."""

# Version
VERSION = "0.8.0"

# Documentation tags
DOCSIBLE_START_TAG = "<!-- DOCSIBLE START -->"
DOCSIBLE_END_TAG = "<!-- DOCSIBLE END -->"
GENERATED_TAG = "<!-- DOCSIBLE GENERATED -->"
MANUAL_TAG = "<!-- MANUALLY MAINTAINED -->"
MIXED_TAG = "<!-- DOCSIBLE GENERATED + MANUAL ADDITIONS -->"

# File names
DEFAULT_README = "README.md"
DEFAULT_CONFIG_FILE = ".docsible.yml"
DOCSIBLE_METADATA_FILE = ".docsible"

# YAML extensions
YAML_EXTENSIONS = ['.yml', '.yaml']

# Ansible directory defaults
DEFAULT_DEFAULTS_DIR = "defaults"
DEFAULT_VARS_DIR = "vars"
DEFAULT_TASKS_DIR = "tasks"
DEFAULT_META_DIR = "meta"
DEFAULT_HANDLERS_DIR = "handlers"
DEFAULT_LIBRARY_DIR = "library"
DEFAULT_LOOKUP_PLUGINS_DIR = "lookup_plugins"
DEFAULT_FILTER_PLUGINS_DIR = "filter_plugins"
DEFAULT_MODULE_UTILS_DIR = "module_utils"
DEFAULT_TEMPLATES_DIR = "templates"
DEFAULT_ROLES_DIR = "roles"

# Ansible file names
DEFAULT_META_FILE = "main"
DEFAULT_ARGUMENT_SPECS_FILE = "argument_specs"
DEFAULT_TEST_PLAYBOOK = "tests/test.yml"

# Mermaid diagram settings
MAX_DIAGRAM_LINES_BEFORE_SIMPLIFICATION = 20
MAX_TASK_NAME_LENGTH = 40

# Collection markers
COLLECTION_MARKER_FILES = ["galaxy.yml", "galaxy.yaml"]
ROLE_MARKER_FILES = ["meta/main.yml", "meta/main.yaml"]

# Timestamp format for backups
BACKUP_TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"
