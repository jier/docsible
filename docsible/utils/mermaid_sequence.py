"""
Mermaid sequence diagram generation for Ansible playbooks and roles.
Provides both high-level architecture and detailed execution flow visualizations.
"""
import re
from typing import List, Dict, Any, Optional


def sanitize_participant_name(text: str) -> str:
    """Sanitize text to be used as a Mermaid participant name."""
    # Remove special characters, keep alphanumeric and underscores
    return re.sub(r'[^a-zA-Z0-9_]', '_', text)


def sanitize_note_text(text: str, max_length: int = 50) -> str:
    """Sanitize text for use in notes and messages."""
    # Truncate and escape special characters
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text.replace('"', "'").replace('\n', ' ')


def generate_mermaid_sequence_playbook_high_level(playbook: List[Dict], role_meta: Optional[Dict] = None) -> str:
    """
    Generate high-level sequence diagram showing playbook → roles interaction.

    Shows:
    - Playbook execution flow
    - Role dependencies (from meta/main.yml)
    - Pre-tasks, roles, tasks, post-tasks, handlers phases
    - Role includes/imports

    Args:
        playbook: Parsed playbook YAML structure
        role_meta: Optional role metadata for dependency information

    Returns:
        Mermaid sequence diagram as string
    """
    diagram = "sequenceDiagram\n"
    diagram += "    participant User\n"
    diagram += "    participant Playbook\n"

    # Track participants (roles and handlers)
    participants = set()

    # Analyze playbook structure to identify all participants
    for play in playbook:
        # Add roles as participants
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

        # Pre-tasks
        pre_tasks = play.get("pre_tasks", [])
        if pre_tasks:
            diagram += f"    Note over Playbook: Pre-tasks ({len(pre_tasks)} tasks)\n"
            diagram += "    Playbook->>Playbook: Execute pre-tasks\n\n"

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

        # Tasks
        tasks = play.get("tasks", [])
        if tasks:
            diagram += f"    Note over Playbook: Tasks ({len(tasks)} tasks)\n"
            diagram += "    Playbook->>Playbook: Execute tasks\n"

            # Check for handler notifications in tasks
            for task in tasks:
                if isinstance(task, dict) and 'notify' in task:
                    if has_handlers:
                        diagram += "    Playbook->>Handlers: Notify\n"
                    break
            diagram += "\n"

        # Post-tasks
        post_tasks = play.get("post_tasks", [])
        if post_tasks:
            diagram += f"    Note over Playbook: Post-tasks ({len(post_tasks)} tasks)\n"
            diagram += "    Playbook->>Playbook: Execute post-tasks\n\n"

        # Handlers
        if has_handlers:
            diagram += "    Note over Playbook,Handlers: Flush handlers\n"
            diagram += "    Playbook->>+Handlers: Execute all notified handlers\n"
            diagram += "    Handlers-->>-Playbook: Complete\n\n"

    diagram += "    Playbook-->>User: Playbook complete\n"
    diagram += "    deactivate Playbook\n"

    return diagram


def generate_mermaid_sequence_role_detailed(role_info: Dict[str, Any], include_handlers: bool = True) -> str:
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

    diagram += f"    participant Playbook\n"
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
        for task in tasks:
            task_name = task.get('name', 'Unnamed task')
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
                    diagram += f"    alt Block fails\n"
                    diagram += f"        {task_file_participant}->>{task_file_participant}: Execute rescue\n"
                    diagram += f"    end\n"

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
