# Docsible Configuration Guide

This guide explains how to configure Docsible to work with various Ansible project structures.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration Priority](#configuration-priority)
- [Project Types](#project-types)
- [Configuration Reference](#configuration-reference)
- [Examples](#examples)
- [Migration Guide](#migration-guide)

## Overview

Starting with version 0.8.0, Docsible supports flexible project structures through:

1. **Auto-detection**: Automatically detects standard roles, collections, AWX projects, and monorepos
2. **Configuration files**: Optional `.docsible.yml` to customize paths and settings
3. **CLI overrides**: Command-line flags take precedence over all other settings

**Backward Compatibility**: Existing projects work without any changes. The default behavior remains the same as previous versions.

## Quick Start

### For Standard Projects (No Configuration Needed)

If your project follows the standard Ansible structure, just run Docsible as usual:

```bash
# Standard role
docsible --role ./my-role

# Standard collection
docsible --collection ./my-collection
```

### For Custom Structures

1. Generate an example configuration file:

```bash
docsible-init-config --path /path/to/your/project
```

2. Edit `.docsible.yml` to match your structure:

```yaml
structure:
  roles_dir: 'ansible/roles'  # For monorepos
  defaults_dir: 'role_defaults'  # If you use custom directory names
```

3. Run Docsible:

```bash
docsible --role ./my-role
```

## Configuration Priority

Docsible uses a priority system for configuration:

```
CLI Flags > .docsible.yml > Auto-detection > Built-in Defaults
```

**Example**:
- Built-in default for `defaults_dir`: `defaults`
- Auto-detection finds: `defaults`
- `.docsible.yml` specifies: `role_defaults`
- CLI flag specifies: `custom_defaults`
- **Result**: Uses `custom_defaults`

## Project Types

Docsible automatically detects the following project types:

### 1. Standard Role

**Structure**:
```
my-role/
├── defaults/
│   └── main.yml
├── vars/
│   └── main.yml
├── tasks/
│   └── main.yml
├── meta/
│   └── main.yml
└── README.md
```

**Detection**: Has at least one of: `tasks/`, `defaults/`, `vars/`, `meta/`

### 2. Collection

**Structure**:
```
my-collection/
├── galaxy.yml
├── roles/
│   ├── role1/
│   └── role2/
└── README.md
```

**Detection**: Has `galaxy.yml` or `galaxy.yaml` file

### 3. Multi-Role Repository

**Structure**:
```
my-roles-repo/
├── roles/
│   ├── role1/
│   │   ├── tasks/
│   │   └── defaults/
│   └── role2/
│       ├── tasks/
│       └── vars/
└── README.md
```

**Detection**: Has `roles/` directory at root, but no `galaxy.yml` (not a formal collection)

**Use Case**: Regular repositories that organize multiple roles in a `roles/` folder without being an official Ansible collection.

**Usage**:
```bash
docsible --collection ./my-roles-repo
```

### 4. AWX Project

**Structure**:
```
awx-project/
├── roles/
│   ├── role1/
│   └── role2/
├── inventory/
│   └── hosts
├── project.yml
└── README.md
```

**Detection**: Has **BOTH** `roles/` directory **AND** `inventory/` or `inventories/` directory

### 5. Monorepo

**Structure**:
```
monorepo/
├── ansible/
│   └── roles/
│       ├── role1/
│       └── role2/
├── playbooks/
└── README.md
```

**Detection**: Has roles in nested paths like `ansible/roles/`, `playbooks/roles/`, `automation/roles/`

## Configuration Reference

### Complete `.docsible.yml` Example

```yaml
structure:
  # Directory names (relative to role root)
  defaults_dir: 'defaults'           # Where default variables are stored
  vars_dir: 'vars'                   # Where role variables are stored
  tasks_dir: 'tasks'                 # Where task files are located
  meta_dir: 'meta'                   # Where role metadata is stored
  handlers_dir: 'handlers'           # Where handlers are located (for collections/monorepos)
   
  
  # Custom modules and plugins
  library_dir: 'library'                     # Custom Ansible modules
  lookup_plugins_dir: 'lookup_plugins'       # Custom lookup plugins 
  templates_dir: 'templates'         # Where Jinja2 templates are located

  # For collections and monorepos
  roles_dir: 'roles'                 # Where roles are located

  # File names (without extensions)
  meta_file: 'main'                  # Meta file name (meta/main.yml)
  argument_specs_file: 'argument_specs'  # Argument specs file name

  # Test playbook
  test_playbook: 'tests/test.yml'    # Default test playbook location

  # File extensions
  yaml_extensions: ['.yml', '.yaml'] # YAML file extensions to scan
```

### Configuration Fields

#### Standard Role Directories

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `defaults_dir` | string | `defaults` | Directory containing default variables |
| `vars_dir` | string | `vars` | Directory containing role variables |
| `tasks_dir` | string | `tasks` | Directory containing task files |
| `meta_dir` | string | `meta` | Directory containing role metadata |
| `handlers_dir` | string | `handlers` | Directory containing handlers |

#### Custom Modules and Plugins

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `library_dir` | string | `library` | Custom Ansible modules (Python files) |
| `lookup_plugins_dir` | string | `lookup_plugins` | Custom lookup plugins |
| `templates_dir` | string | `templates` | Jinja2 template files |

#### Multi-Role Projects

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `roles_dir` | string | `roles` | Directory containing roles (collections/monorepos) |

#### Metadata Files

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `meta_file` | string | `main` | Name of meta file (without extension) |

#### Testing

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `test_playbook` | string | `tests/test.yml` | Path to test playbook |

#### File Extensions

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `yaml_extensions` | list | `['.yml', '.yaml']` | Supported YAML file extensions |

## Examples

### Example 1: Monorepo with Custom Structure

**Directory Structure**:
```
company-automation/
├── ansible/
│   └── roles/
│       ├── webserver/
│       ├── database/
│       └── monitoring/
└── docs/
```

**Configuration** (`.docsible.yml` in `company-automation/`):
```yaml
structure:
  roles_dir: 'ansible/roles'
```

**Usage**:
```bash
cd company-automation
docsible --collection .
```

### Example 2: Custom Directory Names

**Directory Structure**:
```
custom-role/
├── role_defaults/       # Instead of 'defaults/'
│   └── main.yml
├── variables/           # Instead of 'vars/'
│   └── main.yml
├── playbooks/           # Instead of 'tasks/'
│   └── main.yml
└── metadata/            # Instead of 'meta/'
    └── main.yml
```

**Configuration** (`.docsible.yml` in `custom-role/`):
```yaml
structure:
  defaults_dir: 'role_defaults'
  vars_dir: 'variables'
  tasks_dir: 'playbooks'
  meta_dir: 'metadata'
```

**Usage**:
```bash
docsible --role ./custom-role
```

### Example 3: Multi-Role Repository

**Directory Structure**:
```
ansible-roles/
├── roles/
│   ├── webserver/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   ├── database/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── vars/
│   │       └── main.yml
│   └── loadbalancer/
│       └── tasks/
│           └── main.yml
└── README.md
```

**Configuration**: Not needed (auto-detected as multi-role repository)

**Usage**:
```bash
# Documents all roles in the roles/ directory
docsible --collection ./ansible-roles
```

**Result**: Creates a README.md at the root and individual role documentation in each role directory.

### Example 4: AWX Project

**Directory Structure**:
```
awx-project/
├── roles/
│   ├── provision/
│   └── deploy/
├── inventory/
│   └── production
└── project.yml
```

**Configuration**: Not needed (auto-detected as AWX project)

**Usage**:
```bash
docsible --collection ./awx-project
```

### Example 5: Multiple Collections in Monorepo

**Directory Structure**:
```
ansible-monorepo/
├── collections/
│   ├── namespace1.collection1/
│   │   ├── galaxy.yml
│   │   └── roles/
│   └── namespace2.collection2/
│       ├── galaxy.yml
│       └── roles/
└── README.md
```

**Configuration**: Not needed (auto-detects multiple collections)

**Usage**:
```bash
cd ansible-monorepo
docsible --collection .
```

All `galaxy.yml` files will be found and each collection documented.

### Example 6: Support Both .yml and .yaml

By default, Docsible scans both `.yml` and `.yaml` extensions. No configuration needed.

**Supported Files**:
- `meta/main.yml` ✓
- `meta/main.yaml` ✓
- `tasks/install.yml` ✓
- `tasks/configure.yaml` ✓

### Example 7: Plugin-Heavy Role for External Systems

For roles that interact with external systems using custom modules and plugins:

**Directory Structure**:
```
external-api-role/ 
├── defaults/ 
│ └── main.yml 
├── tasks/ 
│ └── main.yml 
├── library/ # Custom modules for API interaction 
│ ├── api_client.py 
│ └── resource_manager.py 
├── lookup_plugins/ # Lookups for fetching external data 
│ └── api_lookup.py 
└── meta/ 
└── main.yml
```

**Configuration** (`.docsible.yml`):
```yaml
structure:
  # Standard directories
  defaults_dir: 'defaults'
  vars_dir: 'vars'
  tasks_dir: 'tasks'
  meta_dir: 'meta'

  # Plugin directories (where most custom code lives)
  library_dir: 'library'
  lookup_plugins_dir: 'lookup_plugins'
```
**Usage**:
```bash
docsible --role ./external-api-role
```
Use Case: Roles that execute commands on external systems via APIs rather than managing local files. Common for cloud providers, SaaS platforms, or infrastructure APIs where custom modules and lookups are essential.

## Variable Comment Tags

Docsible extracts metadata from comments in variable files. Both `-` and `_` separators are supported:

### Supported Tags

```yaml
# title: Database Configuration
# description: PostgreSQL database settings
# required: yes
# choices: postgresql, mysql, mariadb
# type: string
database_type: postgresql

# description-lines:
# This is a multi-line description
# that spans multiple lines
# and supports detailed explanations
# end
database_host: localhost

# description_lines:
# Alternative underscore syntax also works
# for multi-line descriptions
# end
database_port: 5432
```

### Tag Syntax Rules

- **Case-insensitive**: `Title:`, `title:`, `TITLE:` all work
- **Separator flexibility**: Both `-` and `_` are supported
  - `description-lines:` ✓
  - `description_lines:` ✓
- **Multi-line descriptions**: Use `description-lines:` ... `# end`

## CLI Commands

### Main Command: `docsible`

Generate documentation for roles or collections:

```bash
# Document a role
docsible --role ./my-role

# Document a collection
docsible --collection ./my-collection

# With custom options
docsible --role ./my-role --graph --comments --task-line
```

### New Command: `docsible-init-config`

Generate an example `.docsible.yml` configuration file:

```bash
# Create config in current directory
docsible-init-config

# Create config in specific directory
docsible-init-config --path /path/to/project

# Overwrite existing config
docsible-init-config --force
```

## Migration Guide

### Migrating from Pre-0.8.0 Versions

**Good News**: No migration needed! Your existing projects will work exactly as before.

### Optional: Add Configuration for Custom Structures

If you want to document projects with non-standard structures:

1. **Generate config template**:
   ```bash
   cd /path/to/your/project
   docsible-init-config
   ```

2. **Customize** `.docsible.yml` to match your structure

3. **Test** the configuration:
   ```bash
   docsible --role .
   ```

4. **Commit** `.docsible.yml` to your repository

## Troubleshooting

### Configuration Not Loading

**Problem**: Changes in `.docsible.yml` are not being applied

**Solutions**:
- Ensure `.docsible.yml` is in the project root (where you run docsible)
- Check YAML syntax: run `yamllint .docsible.yml`
- Verify indentation (use spaces, not tabs)
- Check the console output for `[INFO] Loaded configuration from ...`

### Roles Not Found

**Problem**: Docsible can't find roles in your monorepo

**Solution**:
Add `roles_dir` to `.docsible.yml`:
```yaml
structure:
  roles_dir: 'path/to/roles'
```

### Custom Directory Not Detected

**Problem**: Docsible can't find your custom `defaults/` directory

**Solution**:
Specify the custom directory name:
```yaml
structure:
  defaults_dir: 'your_custom_name'
```

## Advanced Usage

### Debugging Configuration

To see what configuration Docsible is using, the ProjectStructure class provides a `to_dict()` method for debugging (developers can access this programmatically).

### Extending for New Project Types

The `ProjectStructure` class in `docsible/utils/project_structure.py` can be extended to support additional project patterns. See the source code for implementation details.

## Support

- **GitHub Issues**: https://github.com/docsible/docsible/issues
- **Documentation**: https://github.com/docsible/docsible
- **Examples**: See the `examples/` directory (if available)

## See Also

- [README.md](README.md) - Main documentation
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
