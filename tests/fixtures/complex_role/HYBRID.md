<!-- DOCSIBLE METADATA
generated_at: 2025-12-19T10:28:19.220630+00:00Z
docsible_version: 0.8.0
role_hash: 9f5db66940d046875aea45c86aa4d2051bdc813d4035e3e95df1278db8f8758a
-->
<!-- DOCSIBLE START -->


# complex_role
<!-- MANUALLY MAINTAINED -->
> **Note**: Replace this section with your role's description
>
> Brief description of role purpose and scope. Explain what problem this role solves
> and what it accomplishes.

## Quick Start
<!-- MANUALLY MAINTAINED -->
Minimal example for immediate usage:
```yaml
- hosts: servers
  roles:
    - { role: complex_role, variable_key: "value" }
```

## Architecture Overview
<!-- MANUALLY MAINTAINED -->
> **Note**: Add high-level explanation of what the role does and how components interact

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

---

## Role Complexity Analysis

**Complexity Level:** <span style="color: orange">MEDIUM</span>

### Metrics

| Metric | Value |
|--------|-------|
| Total Tasks | 13 |
| Task Files | 4 |
| Handlers | 3 |
| Conditional Tasks | 3 (23%) |
| Error Handlers | 0 |
| Max Tasks per File | 5 |
| Role Dependencies | 2 |
| Task Includes | 3 |

### External Integrations (1)

This role integrates with external systems:

**1. REST APIs** (api)
- **Modules Used:** `ansible.builtin.get_url`
- **Tasks Count:** 1

### Composition Score

**Internal Orchestration:** 7 (Medium)
- Role Dependencies: 2
- Task Includes: 3

### Recommendations
- ✅ Role complexity is well-managed - standard documentation is sufficient

### Visualization Strategy

**For MEDIUM roles** (13 tasks):
- ✅ State diagrams show workflow phases
- ✅ Sequence diagrams show detailed execution
- ✅ Component hierarchy shows task organization

---


## Simplification Opportunities

**Overall Health Score:** <span style="color: green">98/100</span>

This role has **1** potential improvement:
- 🚨 Critical: 0
- ⚠️  Warnings: 0
- 💡 Suggestions: 1

### 💡 Optional Improvements

<details>
<summary><strong>Magic Values</strong> - Found 2 repeated literal values across tasks</summary>

**Example:**
```yaml

'ansible.builtin.file' used 3 times
'ansible.builtin.include_tasks' used 3 times

```

**Suggestion:**
Replace magic values with variables:

**Instead of hardcoding:**
```yaml
- name: Create directory
  file:
    path: /opt/myapp  # ← Hardcoded
    state: directory

- name: Copy config
  copy:
    dest: /opt/myapp/config.yml  # ← Repeated
```

**Use variables:**
```yaml
# defaults/main.yml
app_install_dir: /opt/myapp
app_config_file: "{{ app_install_dir }}/config.yml"
```

```yaml
# tasks/main.yml
- name: Create directory
  file:
    path: "{{ app_install_dir }}"
    state: directory

- name: Copy config
  copy:
    dest: "{{ app_config_file }}"
```

**Benefits:**
- Single source of truth
- Easy to change paths
- Better for multi-environment deployments

**Expected benefit:** Improves flexibility and reduces change burden
**Files:** `uninstall.yml`, `prerequisites.yml`, `main.yml`

</details>

### Pattern Categories Summary
| Category | Count |
|----------|-------|
| Maintainability | 1 |

### Next Steps
1. **Review optional suggestions** - Fine-tune role to perfection

---


## Task Dependency Matrix

*This role has 13 tasks. The table below shows task relationships for understanding execution dependencies and troubleshooting.*

| Task | File | Module | Requires | Triggers | Error Handling | Sets Facts |
|------|------|--------|----------|----------|----------------|------------|
| Stop application service | `uninstall.yml` | `ansible.builtin.service` | - | - | None | - |
| Remove application directory | `uninstall.yml` | `ansible.builtin.file` | - | - | None | - |
| Remove configuration | `uninstall.yml` | `ansible.builtin.file` | - | - | None | - |
| Download application | `install.yml` | `ansible.builtin.get_url` | - | - | None | - |
| Extract application | `install.yml` | `ansible.builtin.unarchive` | - | - | None | - |
| Install Python dependencies | `install.yml` | `ansible.builtin.pip` | - | - | None | - |
| Install required packages | `prerequisites.yml` | `ansible.builtin.apt` | - | - | None | - |
| Create application directory | `prerequisites.yml` | `ansible.builtin.file` | - | - | None | - |
| Include prerequisites | `main.yml` | `ansible.builtin.include_tasks` | - | - | None | - |
| Install application | `main.yml` | `ansible.builtin.include_tasks` | - | - | None | - |
| Remove application | `main.yml` | `ansible.builtin.include_tasks` | - | - | None | - |
| Configure application | `main.yml` | `ansible.builtin.template` | - | - | None | - |
| Ensure service state | `main.yml` | `ansible.builtin.service` | - | - | None | - |

### How to Use This Table

- **Task**: Task name from the playbook
- **File**: Task file location
- **Module**: Ansible module used
- **Requires**: Variables or facts this task depends on
- **Triggers**: Handlers notified when this task reports changes
- **Error Handling**: Error recovery strategy (rescue/always blocks)
- **Sets Facts**: Variables or facts this task defines for later use

### Dependency Patterns

**Summary Statistics:**
- Total Tasks: 13
- Tasks with Variable Dependencies: 0
- Tasks Triggering Handlers: 0
- Tasks with Error Handling: 0
- Tasks Setting Facts: 0

<details>
<summary><b>💡 Understanding Task Dependencies</b></summary>

**Variable Dependencies (Requires):**
- Shows which variables/facts must be defined before task execution
- Helpful for understanding task prerequisites
- Critical for troubleshooting "undefined variable" errors

**Handler Triggers:**
- Shows which handlers are notified when task state changes
- Essential for understanding service restart cascades
- Helps identify which tasks trigger notifications

**Error Handling:**
- `rescue`: Task has error recovery logic
- `always`: Task has cleanup logic that always runs
- `rescue + always`: Task has both error recovery and cleanup
- `None`: Task has no explicit error handling

**Facts Set:**
- Variables registered or set by this task
- Available for use by subsequent tasks
- Critical for understanding data flow through the role

</details>

---

## Task Execution Flow
<!-- DOCSIBLE GENERATED -->
> Generated via: `docsible --role . --graph --comments --no-backup`


### Detailed Execution Sequence
This sequence diagram shows the detailed interaction between the role, tasks, includes, and handlers:
```mermaid
sequenceDiagram
    autonumber
    participant Playbook
    participant complex_role
    participant Handlers

    Playbook->>+complex_role: Execute role
    activate complex_role

    participant Tasks_uninstall_yml
    Note over complex_role,Tasks_uninstall_yml: File: uninstall.yml
    complex_role->>+Tasks_uninstall_yml: Load tasks

    Tasks_uninstall_yml->>Tasks_uninstall_yml: Stop application service
    Note right of Tasks_uninstall_yml: ansible.builtin.service

    Tasks_uninstall_yml->>Tasks_uninstall_yml: Remove application directory
    Note right of Tasks_uninstall_yml: ansible.builtin.file

    Tasks_uninstall_yml->>Tasks_uninstall_yml: Remove configuration
    Note right of Tasks_uninstall_yml: ansible.builtin.file

    Tasks_uninstall_yml-->>-complex_role: Tasks complete

    participant Tasks_install_yml
    Note over complex_role,Tasks_install_yml: File: install.yml
    complex_role->>+Tasks_install_yml: Load tasks

    Tasks_install_yml->>Tasks_install_yml: Download application
    Note right of Tasks_install_yml: ansible.builtin.get_url

    Tasks_install_yml->>Tasks_install_yml: Extract application
    Note right of Tasks_install_yml: ansible.builtin.unarchive

    Tasks_install_yml->>Tasks_install_yml: Install Python dependencies
    Note right of Tasks_install_yml: ansible.builtin.pip

    Tasks_install_yml-->>-complex_role: Tasks complete

    participant Tasks_prerequisites_yml
    Note over complex_role,Tasks_prerequisites_yml: File: prerequisites.yml
    complex_role->>+Tasks_prerequisites_yml: Load tasks

    Tasks_prerequisites_yml->>Tasks_prerequisites_yml: Install required packages
    Note right of Tasks_prerequisites_yml: ansible.builtin.apt

    Tasks_prerequisites_yml->>Tasks_prerequisites_yml: Create application directory
    Note right of Tasks_prerequisites_yml: ansible.builtin.file

    Tasks_prerequisites_yml-->>-complex_role: Tasks complete

    participant Tasks_main_yml
    Note over complex_role,Tasks_main_yml: File: main.yml
    complex_role->>+Tasks_main_yml: Load tasks

    participant Include_unknown
    Tasks_main_yml->>Include_unknown: ansible.builtin.include_tasks: unknown
    activate Include_unknown
    Note over Include_unknown: Include prerequisites
    Include_unknown-->>Tasks_main_yml: Complete
    deactivate Include_unknown

    Tasks_main_yml->>Include_unknown: ansible.builtin.include_tasks: unknown
    activate Include_unknown
    Note over Include_unknown: Install application
    Include_unknown-->>Tasks_main_yml: Complete
    deactivate Include_unknown

    Tasks_main_yml->>Include_unknown: ansible.builtin.include_tasks: unknown
    activate Include_unknown
    Note over Include_unknown: Remove application
    Include_unknown-->>Tasks_main_yml: Complete
    deactivate Include_unknown

    Tasks_main_yml->>Tasks_main_yml: Configure application
    Note right of Tasks_main_yml: ansible.builtin.template

    Tasks_main_yml->>Tasks_main_yml: Ensure service state
    Note right of Tasks_main_yml: ansible.builtin.service

    Tasks_main_yml-->>-complex_role: Tasks complete

    Note over complex_role,Handlers: Execute notified handlers
    complex_role->>+Handlers: Flush handlers
    Handlers->>Handlers: Restart application
    Handlers->>Handlers: Reload application
    Handlers->>Handlers: Clear cache
    Handlers-->>-complex_role: Handlers complete

    deactivate complex_role
    complex_role-->>-Playbook: Role complete

```
---


### State Transition Diagram
This diagram shows the workflow phases and state transitions of the role.
```mermaid
---
title: complex_role - State Transitions
---
stateDiagram-v2
    [*] --> Install
    Install --> Configure: when packages installed
    Configure --> Validate
    Stop --> Cleanup: when stopped
    Validate --> Execute
    note right of Stop: 1 tasks with state management
    note right of Cleanup: 2 tasks with state management
    note right of Configure: 2 tasks with state management
    note right of Install: 5 tasks with state management
    note right of Validate: 1 tasks with state management
    Cleanup --> [*]
```


### Component Architecture (COMPLEX Complexity)

*Generated for COMPLEX roles to show internal structure and data flow.*

```mermaid
graph TB
    subgraph Variables
        defaults["📋 Defaults<br/>20 variables"]
    end

    subgraph Tasks
        tasks_uninstall_yml["⚙️ uninstall.yml<br/>3 tasks"]
        tasks_install_yml["⚙️ install.yml<br/>3 tasks"]
        tasks_prerequisites_yml["⚙️ prerequisites.yml<br/>2 tasks"]
        tasks_main_yml["⚙️ main.yml<br/>5 tasks"]
    end

    handlers["🔔 Handlers<br/>3 handlers"]

    external["🌐 External Systems<br/>REST APIs"]

    %% Data Flow
    defaults --> tasks_uninstall_yml
    tasks_uninstall_yml --> tasks_main_yml
    tasks_main_yml -."notify".-> handlers

    %% Styling
    classDef varStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef taskStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef handlerStyle fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef externalStyle fill:#ffebee,stroke:#c62828,stroke-width:2px

    class defaults varStyle
    class handlers handlerStyle
    class external externalStyle
    class tasks_uninstall_yml taskStyle
    class tasks_install_yml taskStyle
    class tasks_prerequisites_yml taskStyle
    class tasks_main_yml taskStyle
```

**Legend:**
- 📋 Variables: Default values and configuration
- ⚙️ Tasks: Execution units organized by file
- 🔔 Handlers: Triggered by task notifications
- 🌐 External Systems: Third-party integrations


### Tasks in `uninstall.yml` (Flowchart)
```mermaid
flowchart TD
Start
classDef block stroke:#3498db,stroke-width:2px;
classDef task stroke:#4b76bb,stroke-width:2px;
classDef includeTasks stroke:#16a085,stroke-width:2px;
classDef importTasks stroke:#34495e,stroke-width:2px;
classDef includeRole stroke:#2980b9,stroke-width:2px;
classDef importRole stroke:#699ba7,stroke-width:2px;
classDef includeVars stroke:#8e44ad,stroke-width:2px;
classDef rescue stroke:#665352,stroke-width:2px;
  Start-->|Task| Stop_application_service0[stop application service]:::task
  Stop_application_service0-->|Task| Remove_application_directory1[remove application directory]:::task
  Remove_application_directory1-->|Task| Remove_configuration2[remove configuration]:::task
  Remove_configuration2-->End
```


### Tasks in `install.yml` (Flowchart)
```mermaid
flowchart TD
Start
classDef block stroke:#3498db,stroke-width:2px;
classDef task stroke:#4b76bb,stroke-width:2px;
classDef includeTasks stroke:#16a085,stroke-width:2px;
classDef importTasks stroke:#34495e,stroke-width:2px;
classDef includeRole stroke:#2980b9,stroke-width:2px;
classDef importRole stroke:#699ba7,stroke-width:2px;
classDef includeVars stroke:#8e44ad,stroke-width:2px;
classDef rescue stroke:#665352,stroke-width:2px;
  Start-->|Task| Download_application0[download application]:::task
  Download_application0-->|Task| Extract_application1[extract application]:::task
  Extract_application1-->|Task| Install_Python_dependencies2[install python dependencies]:::task
  Install_Python_dependencies2-->End
```


### Tasks in `prerequisites.yml` (Flowchart)
```mermaid
flowchart TD
Start
classDef block stroke:#3498db,stroke-width:2px;
classDef task stroke:#4b76bb,stroke-width:2px;
classDef includeTasks stroke:#16a085,stroke-width:2px;
classDef importTasks stroke:#34495e,stroke-width:2px;
classDef includeRole stroke:#2980b9,stroke-width:2px;
classDef importRole stroke:#699ba7,stroke-width:2px;
classDef includeVars stroke:#8e44ad,stroke-width:2px;
classDef rescue stroke:#665352,stroke-width:2px;
  Start-->|Task| Install_required_packages0[install required packages]:::task
  Install_required_packages0-->|Task| Create_application_directory1[create application directory]:::task
  Create_application_directory1-->End
```


### Tasks in `main.yml` (Flowchart)
```mermaid
flowchart TD
Start
classDef block stroke:#3498db,stroke-width:2px;
classDef task stroke:#4b76bb,stroke-width:2px;
classDef includeTasks stroke:#16a085,stroke-width:2px;
classDef importTasks stroke:#34495e,stroke-width:2px;
classDef includeRole stroke:#2980b9,stroke-width:2px;
classDef importRole stroke:#699ba7,stroke-width:2px;
classDef includeVars stroke:#8e44ad,stroke-width:2px;
classDef rescue stroke:#665352,stroke-width:2px;
  Start-->|Include task| Include_prerequisites_prerequisites_yml_0[include prerequisites<br>include_task: prerequisites yml]:::includeTasks
  Include_prerequisites_prerequisites_yml_0-->|Include task| Install_application_install_yml_1[install application<br>When: **state     present**<br>include_task: install yml]:::includeTasks
  Install_application_install_yml_1-->|Include task| Remove_application_uninstall_yml_2[remove application<br>When: **state     absent**<br>include_task: uninstall yml]:::includeTasks
  Remove_application_uninstall_yml_2-->|Task| Configure_application3[configure application<br>When: **state     present**]:::task
  Configure_application3-->|Task| Ensure_service_state4[ensure service state]:::task
  Ensure_service_state4-->End
```


---


### Handlers
| Handler Name | Module | Listens To | File |
|--------------|--------|------------|------|
| Restart application | ansible.builtin.service | N/A | main.yml |
| Reload application | ansible.builtin.service | N/A | main.yml |
| Clear cache | ansible.builtin.command | clear cache | main.yml |


---


## Role Variables
<!-- DOCSIBLE GENERATED -->

### Default Variables
The following variables are defined in `defaults/` with their default values:
#### File: `defaults/main.yml`

| Variable | Default Value | Type | Description |
|----------|---------------|------|-------------|
| `title` | *See YAML* | str |  |
| `description` | *See YAML* | str |  |
| `state` | *See YAML* | dict |  |
| `state.default` | *See YAML* | str |  |
| `state.choices` | *See YAML* | list |  |
| `state.choices.0` | *See YAML* | str |  |
| `state.choices.1` | *See YAML* | str |  |
| `state.description` | *See YAML* | str |  |
| `app_name` | *See YAML* | str |  |
| `app_version` | *See YAML* | str |  |
| `app_port` | `3000` | int |  |
| `database_config` | *See YAML* | dict |  |
| `database_config.host` | *See YAML* | str |  |
| `database_config.port` | `5432` | int |  |
| `database_config.name` | *See YAML* | str |  |
| `database_config.user` | *See YAML* | str |  |
| `feature_flags` | *See YAML* | dict |  |
| `feature_flags.enable_cache` | `True` | bool |  |
| `feature_flags.enable_monitoring` | `False` | bool |  |
| `feature_flags.debug_mode` | `False` | bool |  |


---


## Dependencies
<!-- DOCSIBLE GENERATED + MANUAL ADDITIONS -->


### Role Dependencies

- `common`

- `hashi_vault`


### Execution Order Notes
<!-- MANUALLY MAINTAINED -->
> **Note**: Add important sequencing information and dependency rationale here
>
> Example:
> - This role must run after `common` role to ensure base packages are installed
> - Database initialization tasks depend on the service being started first
> - Configuration changes trigger handler restarts automatically

---


## Example Playbooks
<!-- MANUALLY MAINTAINED -->
### Basic Usage
```yaml
- hosts: servers
  roles:
    - role: complex_role
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
    - complex_role
```

### Multiple Environments
```yaml
# Production
- hosts: production_servers
  roles:
    - role: complex_role
      environment: production

# Staging
- hosts: staging_servers
  roles:
    - role: complex_role
      environment: staging
```
---


## Task Details
<!-- DOCSIBLE GENERATED -->

### File: `tasks/uninstall.yml`

| Task Name | Module | Description |
|-----------|--------|-------------|
| Stop application service | ansible.builtin.service | |
| Remove application directory | ansible.builtin.file | |
| Remove configuration | ansible.builtin.file | |


### File: `tasks/install.yml`

| Task Name | Module | Description |
|-----------|--------|-------------|
| Download application | ansible.builtin.get_url | |
| Extract application | ansible.builtin.unarchive | |
| Install Python dependencies | ansible.builtin.pip | |


### File: `tasks/prerequisites.yml`

| Task Name | Module | Description |
|-----------|--------|-------------|
| Install required packages | ansible.builtin.apt | |
| Create application directory | ansible.builtin.file | |


### File: `tasks/main.yml`

| Task Name | Module | Description |
|-----------|--------|-------------|
| Include prerequisites | ansible.builtin.include_tasks | |
| Install application | ansible.builtin.include_tasks | |
| Remove application | ansible.builtin.include_tasks | |
| Configure application | ansible.builtin.template | |
| Ensure service state | ansible.builtin.service | |


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


### Galaxy Info
- **Author**: Test Author
- **Company**: Test Company
- **License**: MIT
- **Min Ansible Version**: 2.1

#### Supported Platforms

- Ubuntu: focal, jammy

- Debian: bullseye


#### Galaxy Tags
test, complex, state-management


---

## License & Author
<!-- MANUALLY MAINTAINED -->

**License**: MIT

**Author**: Test Author


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

<!-- DOCSIBLE END -->