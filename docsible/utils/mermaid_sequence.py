"""
Mermaid sequence diagram generation for Ansible playbooks and roles.
Provides both high-level architecture and detailed execution flow visualizations.
"""
import logging
import re
from typing import List, Dict, Any, Optional

from docsible.utils.mermaid import extract_task_name_from_module

logger = logging.getLogger(__name__)


def sanitize_participant_name(text: str) -> str:
    """Sanitize text to be used as a Mermaid participant name.

    Removes special characters, keeping only alphanumeric and underscores.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for use as Mermaid participant name

    Example:
        >>> sanitize_participant_name("my-role.name")
        'my_role_name'
    """
    # Remove special characters, keep alphanumeric and underscores
    return re.sub(r'[^a-zA-Z0-9_]', '_', text)


def sanitize_note_text(text: str, max_length: int = 50) -> str:
    """Sanitize text for use in notes and messages.

    Truncates to max_length and escapes special characters.

    Args:
        text: Text to sanitize
        max_length: Maximum length before truncation (default: 50)

    Returns:
        Sanitized text safe for use in Mermaid notes/messages

    Example:
        >>> sanitize_note_text('Long text with "quotes"\\nand newlines', 20)
        'Long text with \\'quote...'
    """
    # Truncate and escape special characters
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text.replace('"', "'").replace('\n', ' ')


def generate_mermaid_sequence_playbook_high_level(playbook: List[Dict], role_meta: Optional[Dict] = None) -> str:
    """Generate high-level sequence diagram showing playbook → roles → tasks interaction.

    Shows:
    - Playbook execution flow
    - Role dependencies (from meta/main.yml)
    - Pre-tasks, roles, tasks, post-tasks, handlers phases
    - Individual include_role/import_role/include_tasks/import_tasks
    - Task names

    Args:
        playbook: Parsed playbook YAML structure
        role_meta: Optional role metadata for dependency information

    Returns:
        Mermaid sequence diagram as string

    Example:
        >>> playbook = [{'hosts': 'all', 'roles': ['common']}]
        >>> diagram = generate_mermaid_sequence_playbook_high_level(playbook)
        >>> 'sequenceDiagram' in diagram
        True
    """
    diagram = "sequenceDiagram\n"
    diagram += "    participant User\n"
    diagram += "    participant Playbook\n"

    # Track participants (roles and handlers)
    participants = set()

    # Analyze playbook structure to identify all participants (roles from all sources)
    for play in playbook:
        # Add roles from roles: section
        roles = play.get("roles", [])
        for role in roles:
            if isinstance(role, dict):
                role_name = role.get('role', role.get('name', 'unnamed_role'))
            else:
                role_name = str(role)

            role_name = sanitize_participant_name(role_name)
            if role_name not in participants:
                participants.add(role_name)
                diagram += f"    participant {role_name}\n"

        # Scan tasks for include_role/import_role and add as participants
        for task_section in ["pre_tasks", "tasks", "post_tasks"]:
            tasks = play.get(task_section, [])
            for task in tasks:
                if not isinstance(task, dict):
                    continue

                for role_action in ["include_role", "import_role"]:
                    if role_action in task:
                        role_spec = task[role_action]
                        if isinstance(role_spec, str):
                            role_name = role_spec
                        elif isinstance(role_spec, dict):
                            role_name = role_spec.get("name")
                        else:
                            continue

                        role_name_clean = sanitize_participant_name(role_name)
                        if role_name_clean not in participants:
                            participants.add(role_name_clean)
                            diagram += f"    participant {role_name_clean}\n"

    # Add handlers participant if there are any
    has_handlers = False
    for play in playbook:
        if play.get('handlers') or play.get('tasks', []):
            # Check if any tasks notify handlers
            for task in play.get('tasks', []):
                if isinstance(task, dict) and 'notify' in task:
                    has_handlers = True
                    break

    if has_handlers:
        diagram += "    participant Handlers\n"

    diagram += "\n"

    # Generate sequence
    diagram += "    User->>Playbook: Execute ansible-playbook\n"
    diagram += "    activate Playbook\n\n"

    for play_idx, play in enumerate(playbook):
        hosts = play.get("hosts", "all")
        diagram += f"    Note over Playbook: Play {play_idx + 1}: Target hosts={hosts}\n\n"

        # Pre-tasks - show individual tasks
        pre_tasks = play.get("pre_tasks", [])
        if pre_tasks:
            diagram += f"    Note over Playbook: Pre-tasks ({len(pre_tasks)} tasks)\n"
            diagram = _add_task_details(diagram, pre_tasks, "Playbook", participants, has_handlers)
            diagram += "\n"

        # Role dependencies (if available from meta)
        if role_meta and role_meta.get('dependencies'):
            diagram += "    Note right of Playbook: Role Dependencies\n"
            for dep in role_meta['dependencies']:
                if isinstance(dep, dict):
                    dep_name = dep.get('role', str(dep))
                else:
                    dep_name = str(dep)
                dep_name_clean = sanitize_participant_name(dep_name)

                if dep_name_clean not in participants:
                    participants.add(dep_name_clean)
                    diagram += f"    participant {dep_name_clean}\n"

                diagram += f"    Playbook->>+{dep_name_clean}: Execute (dependency)\n"
                diagram += f"    {dep_name_clean}-->>-Playbook: Complete\n"
            diagram += "\n"

        # Roles
        roles = play.get("roles", [])
        for role in roles:
            if isinstance(role, dict):
                role_name = role.get('role', role.get('name', 'unnamed_role'))
                role_vars = role.get('vars', {})
            else:
                role_name = str(role)
                role_vars = {}

            role_name_clean = sanitize_participant_name(role_name)

            if role_vars:
                diagram += f"    Note over Playbook,{role_name_clean}: Variables: {len(role_vars)} defined\n"

            diagram += f"    Playbook->>+{role_name_clean}: Execute role\n"

            # Check if role notifies handlers
            if has_handlers:
                diagram += f"    {role_name_clean}->>Handlers: Notify (if changed)\n"

            diagram += f"    {role_name_clean}-->>-Playbook: Complete\n\n"

        # Tasks - show individual tasks with include_role/import_role details
        tasks = play.get("tasks", [])
        if tasks:
            diagram += f"    Note over Playbook: Tasks ({len(tasks)} tasks)\n"
            diagram = _add_task_details(diagram, tasks, "Playbook", participants, has_handlers)
            diagram += "\n"

        # Post-tasks - show individual tasks
        post_tasks = play.get("post_tasks", [])
        if post_tasks:
            diagram += f"    Note over Playbook: Post-tasks ({len(post_tasks)} tasks)\n"
            diagram = _add_task_details(diagram, post_tasks, "Playbook", participants, has_handlers)
            diagram += "\n"

        # Handlers
        if has_handlers:
            diagram += "    Note over Playbook,Handlers: Flush handlers\n"
            diagram += "    Playbook->>+Handlers: Execute all notified handlers\n"
            diagram += "    Handlers-->>-Playbook: Complete\n\n"

    diagram += "    Playbook-->>User: Playbook complete\n"
    diagram += "    deactivate Playbook\n"

    return diagram


def _add_task_details(diagram: str, tasks: List[Dict], executor: str, participants: set, has_handlers: bool) -> str:
    """
    Helper function to add task details to sequence diagram.

    Args:
        diagram: The diagram string to append to
        tasks: List of task dictionaries
        executor: Name of the executing participant (e.g., "Playbook")
        participants: Set of known participants
        has_handlers: Whether handlers are present

    Returns:
        Updated diagram string
    """
    for task in tasks:
        if not isinstance(task, dict):
            continue

        # Get task name
        task_name = task.get('name', 'Unnamed task')
        task_name_short = sanitize_note_text(task_name, 40)

        # Check for include_role or import_role
        role_included = False
        for role_action in ["include_role", "import_role"]:
            if role_action in task:
                role_spec = task[role_action]
                if isinstance(role_spec, str):
                    role_name = role_spec
                elif isinstance(role_spec, dict):
                    role_name = role_spec.get("name")
                else:
                    continue

                role_name_clean = sanitize_participant_name(role_name)
                diagram += f"    {executor}->>+{role_name_clean}: {role_action}: {role_name}\n"
                diagram += f"    {role_name_clean}-->>-{executor}: Complete\n"

                # Check for notifications
                if 'notify' in task and has_handlers:
                    diagram += f"    {executor}->>Handlers: Notify\n"
                role_included = True
                break

        if role_included:
            continue

        # Check for include_tasks or import_tasks
        task_included = False
        for task_action in ["include_tasks", "import_tasks"]:
            if task_action in task:
                task_file = task[task_action]
                if isinstance(task_file, str):
                    diagram += f"    {executor}->>{executor}: {task_action}: {task_file}\n"
                elif isinstance(task_file, dict):
                    file_name = task_file.get("file", "unknown")
                    diagram += f"    {executor}->>{executor}: {task_action}: {file_name}\n"

                # Check for notifications
                if 'notify' in task and has_handlers:
                    diagram += f"    {executor}->>Handlers: Notify\n"
                task_included = True
                break

        if task_included:
            continue

        # Regular task
        diagram += f"    {executor}->>{executor}: {task_name_short}\n"

        # Check for notifications
        if 'notify' in task and has_handlers:
            diagram += f"    {executor}->>Handlers: Notify\n"

    return diagram


def generate_mermaid_sequence_role_detailed(role_info: Dict[str, Any], include_handlers: bool = True, simplify_large: bool = True, max_lines: int = 20) -> str:
    """
    Generate detailed sequence diagram showing role → tasks → handlers interaction.

    Shows:
    - Task execution order
    - include_tasks/import_tasks as separate participants
    - include_role/import_role as separate participants
    - Handler notifications and execution
    - Block/rescue/always structures

    Args:
        role_info: Role information dict with tasks, handlers, meta
        include_handlers: Whether to include handler interactions
        simplify_large: If True, simplifies diagrams with more than max_lines
        max_lines: Maximum lines before simplification kicks in

    Returns:
        Mermaid sequence diagram as string
    """
    # First, generate the full diagram
    diagram = _generate_full_sequence_diagram(role_info, include_handlers)

    # Count lines in the diagram
    line_count = diagram.count('\n')

    # If diagram is too large and simplification is enabled, generate simplified version
    if simplify_large and line_count > max_lines:
        diagram = _generate_simplified_sequence_diagram(role_info, include_handlers)

    return diagram


def _detect_state_support(role_info: Dict[str, Any]) -> bool:
    """
    Detect if the role explicitly supports present/absent states.

    Checks:
    - defaults/vars for 'state' variable with present/absent in choices/description
    - tasks using state parameter with present/absent values

    Args:
        role_info: Role information dict

    Returns:
        True if role supports present/absent states
    """
    # Check defaults for state variable
    for defaults_file in role_info.get('defaults', []):
        data = defaults_file.get('data', {})
        if 'state' in data:
            state_info = data['state']
            # Check choices
            choices = state_info.get('choices', '')
            if isinstance(choices, str) and ('present' in choices.lower() and 'absent' in choices.lower()):
                return True
            if isinstance(choices, list) and any('present' in str(c).lower() for c in choices) and any('absent' in str(c).lower() for c in choices):
                return True
            # Check description
            description = state_info.get('description', '')
            if 'present' in str(description).lower() and 'absent' in str(description).lower():
                return True

    # Check vars for state variable
    for vars_file in role_info.get('vars', []):
        data = vars_file.get('data', {})
        if 'state' in data:
            state_info = data['state']
            choices = state_info.get('choices', '')
            if isinstance(choices, str) and ('present' in choices.lower() and 'absent' in choices.lower()):
                return True
            if isinstance(choices, list) and any('present' in str(c).lower() for c in choices) and any('absent' in str(c).lower() for c in choices):
                return True

    # Check tasks for state usage with present/absent
    for task_file_info in role_info.get('tasks', []):
        for task in task_file_info.get('tasks', []):
            if not isinstance(task, dict):
                continue
            # Check if task has state parameter with present/absent
            for key, value in task.items():
                if key == 'state' and isinstance(value, str):
                    if value.lower() in ['present', 'absent']:
                        return True

    return False


def _generate_simplified_sequence_diagram(role_info: Dict[str, Any], include_handlers: bool) -> str:
    """
    Generate simplified sequence diagram for large/complex roles.
    Shows only high-level structure: role → task files → handlers.
    """
    diagram = "sequenceDiagram\n"

    role_name = role_info.get('name', 'Role')
    role_participant = sanitize_participant_name(role_name)

    diagram += "    participant Playbook\n"
    diagram += f"    participant {role_participant}\n"

    # Add handlers if any
    handlers = []
    if include_handlers and role_info.get('handlers'):
        handlers = role_info['handlers']
        diagram += "    participant Handlers\n"

    diagram += "\n"

    # Check for present/absent state support
    supports_states = _detect_state_support(role_info)

    if supports_states:
        # Show alternative flows for present/absent
        diagram += "    alt state: present\n"
        diagram += f"    Playbook->>+{role_participant}: Execute role (ensure present)\n"
        diagram += f"    activate {role_participant}\n"
    else:
        diagram += f"    Playbook->>+{role_participant}: Execute role\n"
        diagram += f"    activate {role_participant}\n"

    diagram += "\n"

    # Process tasks at file level only (no individual task details)
    tasks_data = role_info.get('tasks', [])

    for task_file_info in tasks_data:
        task_file = task_file_info.get('file', 'main.yml')
        tasks = task_file_info.get('tasks', [])

        if not tasks:
            continue

        task_count = len(tasks)

        # Show task file with count
        diagram += f"    {role_participant}->>{role_participant}: Execute {task_file}\n"
        diagram += f"    Note right of {role_participant}: {task_count} tasks\n"

        # Check if any tasks notify handlers
        has_notify = any('notify' in task for task in tasks if isinstance(task, dict))
        if has_notify and include_handlers:
            diagram += f"    {role_participant}->>Handlers: Notify handlers\n"

        diagram += "\n"

    # Execute handlers if any were notified
    if include_handlers and handlers:
        diagram += f"    Note over {role_participant},Handlers: Execute notified handlers\n"
        diagram += f"    {role_participant}->>+Handlers: Flush handlers\n"
        diagram += f"    Note over Handlers: {len(handlers)} handlers\n"
        diagram += f"    Handlers-->>-{role_participant}: Handlers complete\n\n"

    diagram += f"    deactivate {role_participant}\n"
    diagram += f"    {role_participant}-->>-Playbook: Role complete\n"

    # Add "absent" alternative if state support is detected
    if supports_states:
        diagram += "    else state: absent\n"
        diagram += f"    Playbook->>+{role_participant}: Execute role (ensure absent)\n"
        diagram += f"    activate {role_participant}\n"

        # Show simplified task execution for absent
        for task_file_info in tasks_data:
            task_file = task_file_info.get('file', 'main.yml')
            tasks = task_file_info.get('tasks', [])
            if not tasks:
                continue
            task_count = len(tasks)
            diagram += f"    {role_participant}->>{role_participant}: Execute {task_file}\n"
            diagram += f"    Note right of {role_participant}: {task_count} tasks\n"

        diagram += f"    deactivate {role_participant}\n"
        diagram += f"    {role_participant}-->>-Playbook: Role complete\n"
        diagram += "    end\n"

    diagram += f"\n    Note over Playbook: Simplified view - {len(tasks_data)} task files"
    if supports_states:
        diagram += " (supports present/absent)"
    diagram += "\n"

    return diagram


def _generate_full_sequence_diagram(role_info: Dict[str, Any], include_handlers: bool) -> str:
    """
    Generate detailed sequence diagram showing role → tasks → handlers interaction.

    Shows:
    - Task execution order
    - include_tasks/import_tasks as separate participants
    - include_role/import_role as separate participants
    - Handler notifications and execution
    - Block/rescue/always structures

    Args:
        role_info: Role information dict with tasks, handlers, meta
        include_handlers: Whether to include handler interactions

    Returns:
        Mermaid sequence diagram as string
    """
    diagram = "sequenceDiagram\n"

    role_name = role_info.get('name', 'Role')
    role_participant = sanitize_participant_name(role_name)

    diagram += "    participant Playbook\n"
    diagram += f"    participant {role_participant}\n"

    # Track all participants (tasks files, includes, roles, handlers)
    participants = {role_participant}

    # Collect handlers
    handlers = []
    if include_handlers and role_info.get('handlers'):
        handlers = role_info['handlers']
        diagram += "    participant Handlers\n"
        participants.add('Handlers')

    diagram += "\n"
    diagram += f"    Playbook->>+{role_participant}: Execute role\n"
    diagram += f"    activate {role_participant}\n\n"

    # Process tasks
    tasks_data = role_info.get('tasks', [])

    for task_file_info in tasks_data:
        task_file = task_file_info.get('file', 'main.yml')
        tasks = task_file_info.get('tasks', [])

        if not tasks:
            continue

        task_file_participant = sanitize_participant_name(f"Tasks_{task_file.replace('/', '_').replace('.', '_')}")

        # Add task file as participant if not already there
        if task_file_participant not in participants:
            diagram += f"    participant {task_file_participant}\n"
            participants.add(task_file_participant)

        diagram += f"    Note over {role_participant},{task_file_participant}: File: {task_file}\n"
        diagram += f"    {role_participant}->>+{task_file_participant}: Load tasks\n\n"

        # Process each task
        for task_idx, task in enumerate(tasks):
            # Get task name - use extract_task_name_from_module for unnamed tasks
            if 'name' not in task or not task['name']:
                # Try to extract from original task data if available
                original_task = task_file_info.get('mermaid', [{}])[task_idx] if task_idx < len(task_file_info.get('mermaid', [])) else task
                task_name = extract_task_name_from_module(original_task, task_idx)
            else:
                task_name = task['name']

            task_module = task.get('module', 'unknown')

            # Sanitize task name for display
            task_display = sanitize_note_text(task_name, 40)

            # Handle include_tasks/import_tasks
            if task_module in ['include_tasks', 'import_tasks', 'ansible.builtin.include_tasks', 'ansible.builtin.import_tasks']:
                include_file = task.get('file', 'unknown')
                include_participant = sanitize_participant_name(f"Include_{include_file.replace('/', '_').replace('.', '_')}")

                if include_participant not in participants:
                    diagram += f"    participant {include_participant}\n"
                    participants.add(include_participant)

                diagram += f"    {task_file_participant}->>{include_participant}: {task_module}: {include_file}\n"
                diagram += f"    activate {include_participant}\n"
                diagram += f"    Note over {include_participant}: {task_display}\n"
                diagram += f"    {include_participant}-->>{task_file_participant}: Complete\n"
                diagram += f"    deactivate {include_participant}\n"

            # Handle include_role/import_role
            elif task_module in ['include_role', 'import_role', 'ansible.builtin.include_role', 'ansible.builtin.import_role']:
                included_role = task.get('name', task.get('role', 'unknown'))
                role_include_participant = sanitize_participant_name(f"Role_{included_role}")

                if role_include_participant not in participants:
                    diagram += f"    participant {role_include_participant}\n"
                    participants.add(role_include_participant)

                diagram += f"    {task_file_participant}->>{role_include_participant}: {task_module}\n"
                diagram += f"    activate {role_include_participant}\n"
                diagram += f"    Note over {role_include_participant}: {task_display}\n"
                diagram += f"    {role_include_participant}-->>{task_file_participant}: Complete\n"
                diagram += f"    deactivate {role_include_participant}\n"

            # Handle block structures
            elif task_module == 'block':
                diagram += f"    Note over {task_file_participant}: Block: {task_display}\n"
                diagram += f"    {task_file_participant}->>{task_file_participant}: Execute block\n"

                # Check for rescue
                if 'rescue' in task:
                    diagram += "    alt Block fails\n"
                    diagram += f"        {task_file_participant}->>{task_file_participant}: Execute rescue\n"
                    diagram += "    end\n"

                # Check for always
                if 'always' in task:
                    diagram += f"    {task_file_participant}->>{task_file_participant}: Execute always\n"

            # Regular task
            else:
                diagram += f"    {task_file_participant}->>{task_file_participant}: {task_display}\n"
                diagram += f"    Note right of {task_file_participant}: {task_module}\n"

            # Check for handler notification
            if include_handlers and 'notify' in task:
                notified = task['notify']
                if isinstance(notified, list):
                    handler_names = ', '.join(notified)
                else:
                    handler_names = str(notified)

                diagram += f"    {task_file_participant}->>Handlers: Notify: {sanitize_note_text(handler_names, 30)}\n"

            diagram += "\n"

        diagram += f"    {task_file_participant}-->>-{role_participant}: Tasks complete\n\n"

    # Execute handlers if any were notified
    if include_handlers and handlers:
        diagram += f"    Note over {role_participant},Handlers: Execute notified handlers\n"
        diagram += f"    {role_participant}->>+Handlers: Flush handlers\n"

        for handler in handlers[:3]:  # Show first 3 handlers to avoid clutter
            handler_name = handler.get('name', 'Handler')
            diagram += f"    Handlers->>Handlers: {sanitize_note_text(handler_name, 40)}\n"

        if len(handlers) > 3:
            diagram += f"    Note over Handlers: ... and {len(handlers) - 3} more handlers\n"

        diagram += f"    Handlers-->>-{role_participant}: Handlers complete\n\n"

    diagram += f"    deactivate {role_participant}\n"
    diagram += f"    {role_participant}-->>-Playbook: Role complete\n"

    return diagram
