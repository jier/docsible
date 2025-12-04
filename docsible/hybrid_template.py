"""
Hybrid README template combining manual sections with auto-generated content.
This template is designed to preserve manually maintained sections while
allowing Docsible to auto-generate technical details.
"""

hybrid_role_template = """# {{ role.name }}

<!-- MANUALLY MAINTAINED -->
> **Note**: Replace this section with your role's description
>
> Brief description of role purpose and scope. Explain what problem this role solves
> and what it accomplates.

## Quick Start

<!-- MANUALLY MAINTAINED -->
Minimal example for immediate usage:

```yaml
- hosts: servers
  roles:
    - { role: {{ role.name }}, variable_key: "value" }
```

## Architecture Overview

<!-- MANUALLY MAINTAINED -->
> **Note**: Add high-level explanation of what the role does and how components interact

{% if sequence_diagram_high_level %}
### Execution Sequence

<!-- DOCSIBLE GENERATED -->
```mermaid
{{ sequence_diagram_high_level }}
```

*This diagram shows how the playbook interacts with roles, dependencies, and handlers.*
{% else %}
> **Note**: Add a high-level architecture diagram below. Use `--graph` flag with a playbook to auto-generate sequence diagram.

```mermaid
graph TD
    A[Role Input] --> B[Validation]
    B --> C[Package Installation]
    C --> D[Configuration]
    D --> E[Service Management]
    E --> F[Handler Triggers]
```

*Customize the mermaid diagram above to match your role's architecture.*
{% endif %}

---

## Task Execution Flow

<!-- DOCSIBLE GENERATED -->
> Generated via: `docsible --role . --graph --comments --no-backup`

{% if sequence_diagram_detailed %}
### Detailed Execution Sequence

This sequence diagram shows the detailed interaction between the role, tasks, includes, and handlers:

```mermaid
{{ sequence_diagram_detailed }}
```

---

{% endif %}

{% if not no_vars %}
{% if role.playbook.graph %}
### Playbook Flow (Flowchart)
```mermaid
{{ role.playbook.graph }}
```
{% endif %}

{% for task_info in role.tasks %}
{% if mermaid_code_per_file.get(task_info.file) %}
### Tasks in `{{ task_info.file }}` (Flowchart)
```mermaid
{{ mermaid_code_per_file[task_info.file] }}
```
{% endif %}
{% endfor %}

{% if not role.tasks and not role.playbook.graph and not sequence_diagram_detailed %}
*No task flow graph generated. Use `--graph` flag to generate task execution diagrams.*
{% endif %}
{% endif %}

---

{% if not no_vars %}
## Role Variables

<!-- DOCSIBLE GENERATED -->

{% if role.defaults %}
### Default Variables

The following variables are defined in `defaults/` with their default values:

{% for defaults_file in role.defaults %}
#### File: `defaults/{{ defaults_file.file }}`

| Variable | Default Value | Type | Description |
|----------|---------------|------|-------------|
{% for key, value in defaults_file.data.items() %}
| `{{ key }}` | {{ '`' + (value.value|string) + '`' if value.value is not mapping and value.value is not sequence else '*See YAML*' }} | {{ value.type }} | {% if value.title %}**{{ value.title }}**<br>{% endif %}{% if value.description %}{{ value.description }}{% endif %}{% if value.required %}<br>**Required:** {{ value.required }}{% endif %}{% if value.choices %}<br>**Choices:** {{ value.choices }}{% endif %} |
{% endfor %}

{% endfor %}
{% else %}
*No default variables defined for this role.*
{% endif %}

{% if role.vars %}
### Role Variables

The following variables are defined in `vars/`:

{% for vars_file in role.vars %}
#### File: `vars/{{ vars_file.file }}`

| Variable | Value | Type | Description |
|----------|-------|------|-------------|
{% for key, value in vars_file.data.items() %}
| `{{ key }}` | {{ '`' + (value.value|string) + '`' if value.value is not mapping and value.value is not sequence else '*See YAML*' }} | {{ value.type }} | {% if value.title %}**{{ value.title }}**<br>{% endif %}{% if value.description %}{{ value.description }}{% endif %} |
{% endfor %}

{% endfor %}
{% endif %}

{% if role.argument_specs %}
### Argument Specifications

{% for spec_name, spec_data in role.argument_specs.items() %}
#### {{ spec_name }}

{% if spec_data.short_description %}
{{ spec_data.short_description }}
{% endif %}

{% if spec_data.options %}
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
{% for option_name, option_data in spec_data.options.items() %}
| `{{ option_name }}` | {{ option_data.type | default('str') }} | {{ 'Yes' if option_data.required else 'No' }} | {{ '`' + (option_data.default|string) + '`' if option_data.default is defined else '-' }} | {{ option_data.description | join(' ') if option_data.description is iterable and option_data.description is not string else option_data.description | default('') }} |
{% endfor %}
{% endif %}

{% endfor %}
{% endif %}

---
{% endif %}

## Dependencies

<!-- DOCSIBLE GENERATED + MANUAL ADDITIONS -->

{% if role.playbook.dependencies %}
### Playbook Role Dependencies

Roles referenced in the playbook (excluding current role):

{% for dep_role in role.playbook.dependencies %}
- `{{ dep_role }}`
{% endfor %}

{% endif %}
{% if role.meta.dependencies %}
### Role Dependencies

This role depends on the following Ansible roles:

{% for dependency in role.meta.dependencies %}
- {% if dependency is mapping %}`{{ dependency.role }}`{% if dependency.version %} (version: {{ dependency.version }}){% endif %}{% else %}`{{ dependency }}`{% endif %}

{% endfor %}
{% else %}
*This role has no role dependencies.*
{% endif %}

### Execution Order Notes

<!-- MANUALLY MAINTAINED -->
> **Note**: Add important sequencing information and dependency rationale here
>
> Example:
> - This role must run after `common` role to ensure base packages are installed
> - Database initialization tasks depend on the service being started first
> - Configuration changes trigger handler restarts automatically

---

{% if not no_vars %}
## Example Playbooks

<!-- MANUALLY MAINTAINED -->

### Basic Usage

```yaml
- hosts: servers
  roles:
    - role: {{ role.name }}
      # Add your basic variables here
      # variable_name: value
```

### Advanced Configuration

```yaml
- hosts: servers
  vars:
    # Add complex variable examples here
    # complex_variable:
    #   - item1: value1
    #     item2: value2
  roles:
    - {{ role.name }}
```

### Multiple Environments

```yaml
# Production
- hosts: production_servers
  roles:
    - role: {{ role.name }}
      environment: production

# Staging
- hosts: staging_servers
  roles:
    - role: {{ role.name }}
      environment: staging
```

---
{% endif %}

{% if not no_vars %}
## Task Details

<!-- DOCSIBLE GENERATED -->

{% for task_info in role.tasks %}
### File: `tasks/{{ task_info.file }}`

{% if task_info.tasks %}
| Task Name | Module | Description |
|-----------|--------|-------------|
{% for task in task_info.tasks %}
| {{ task.name if task.name else '*unnamed*' }} | `{{ task.module }}` | {% if task_info.comments %}{% for comment in task_info.comments %}{% if comment.task_name == task.name %}{{ comment.task_comments }}{% endif %}{% endfor %}{% endif %} |
{% endfor %}
{% endif %}

{% endfor %}

{% if not role.tasks %}
*No tasks found in this role.*
{% endif %}

---

## Testing

<!-- MANUALLY MAINTAINED -->

> **Note**: Add testing instructions here

### Test Environment Setup

```bash
# Example test setup commands
# ansible-playbook tests/test.yml -i tests/inventory
```

### Validation Steps

1. Verify service is running
2. Check configuration files are in place
3. Validate connectivity/functionality

### Molecule Testing (Optional)

```bash
# If using Molecule for testing
# molecule test
```

---
{% endif %}

## Compatibility

<!-- MANUALLY MAINTAINED -->

### Supported Operating Systems

- Ubuntu 20.04, 22.04
- Debian 10, 11
- CentOS 7, 8
- RHEL 7, 8

### Requirements

- **Ansible version**: >= 2.10
- **Python version**: >= 3.6
- **Privilege level**: root/sudo required

### Known Limitations

> **Note**: Document any known issues or limitations here

---

## Role Metadata

<!-- DOCSIBLE GENERATED -->

{% if role.meta %}
{% if role.meta.galaxy_info %}
### Galaxy Info

- **Author**: {{ role.meta.galaxy_info.author | default('Not specified') }}
- **Company**: {{ role.meta.galaxy_info.company | default('Not specified') }}
- **License**: {{ role.meta.galaxy_info.license | default('Not specified') }}
- **Min Ansible Version**: {{ role.meta.galaxy_info.min_ansible_version | default('Not specified') }}

{% if role.meta.galaxy_info.platforms %}
#### Supported Platforms

{% for platform in role.meta.galaxy_info.platforms %}
- {{ platform.name }}{% if platform.versions %}: {{ platform.versions | join(', ') }}{% endif %}

{% endfor %}
{% endif %}

{% if role.meta.galaxy_info.galaxy_tags %}
#### Galaxy Tags

{{ role.meta.galaxy_info.galaxy_tags | join(', ') }}
{% endif %}
{% endif %}
{% endif %}

{% if role.docsible %}
---

## Documentation Metadata

{% if role.docsible.description %}**Description**: {{ role.docsible.description }}{% endif %}

{% if role.docsible.version %}**Version**: {{ role.docsible.version }}{% endif %}

{% if role.docsible.category %}**Category**: {{ role.docsible.category }}{% if role.docsible.subCategory %} > {{ role.docsible.subCategory }}{% endif %}{% endif %}

{% if role.docsible.dt_update %}**Last Updated**: {{ role.docsible.dt_update }}{% endif %}

{% endif %}

---

## License & Author

<!-- MANUALLY MAINTAINED -->

{% if role.meta and role.meta.galaxy_info %}
**License**: {{ role.meta.galaxy_info.license | default('Not specified') }}

**Author**: {{ role.meta.galaxy_info.author | default('Your Name') }}
{% else %}
**License**: Specify your license here (e.g., MIT, Apache 2.0, GPL-3.0)

**Author**: Your Name <your.email@example.com>
{% endif %}

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## Changelog

<!-- MANUALLY MAINTAINED -->

### [Version] - Date

**Added**
- New feature description

**Changed**
- Modified behavior description

**Fixed**
- Bug fix description

---

*This documentation was generated with [Docsible](https://github.com/docsible/docsible)*
"""
