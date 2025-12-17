"""
Mermaid sequence diagram generation for Ansible playbooks.
Generates high-level architecture diagrams showing playbook → roles → tasks interaction.
"""

import logging

from .sanitization import sanitize_note_text, sanitize_participant_name

logger = logging.getLogger(__name__)


def generate_mermaid_sequence_playbook_high_level(
    playbook: list[dict], role_meta: dict | None = None
) -> str:
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
    diagram += "    autonumber\n"
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
                role_name = role.get("role", role.get("name", "unnamed_role"))
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
        if play.get("handlers") or play.get("tasks", []):
            # Check if any tasks notify handlers
            for task in play.get("tasks", []):
                if isinstance(task, dict) and "notify" in task:
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
        diagram += (
            f"    Note over Playbook: Play {play_idx + 1}: Target hosts={hosts}\n\n"
        )

        # Pre-tasks - show individual tasks
        pre_tasks = play.get("pre_tasks", [])
        if pre_tasks:
            diagram += f"    Note over Playbook: Pre-tasks ({len(pre_tasks)} tasks)\n"
            diagram = _add_task_details(
                diagram, pre_tasks, "Playbook", participants, has_handlers
            )
            diagram += "\n"

        # Role dependencies (if available from meta)
        if role_meta and role_meta.get("dependencies"):
            diagram += "    Note right of Playbook: Role Dependencies\n"
            for dep in role_meta["dependencies"]:
                if isinstance(dep, dict):
                    dep_name = dep.get("role", str(dep))
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
                role_name = role.get("role", role.get("name", "unnamed_role"))
                role_vars = role.get("vars", {})
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
            diagram = _add_task_details(
                diagram, tasks, "Playbook", participants, has_handlers
            )
            diagram += "\n"

        # Post-tasks - show individual tasks
        post_tasks = play.get("post_tasks", [])
        if post_tasks:
            diagram += f"    Note over Playbook: Post-tasks ({len(post_tasks)} tasks)\n"
            diagram = _add_task_details(
                diagram, post_tasks, "Playbook", participants, has_handlers
            )
            diagram += "\n"

        # Handlers
        if has_handlers:
            diagram += "    Note over Playbook,Handlers: Flush handlers\n"
            diagram += "    Playbook->>+Handlers: Execute all notified handlers\n"
            diagram += "    Handlers-->>-Playbook: Complete\n\n"

    diagram += "    Playbook-->>User: Playbook complete\n"
    diagram += "    deactivate Playbook\n"

    return diagram


def _add_task_details(
    diagram: str,
    tasks: list[dict],
    executor: str,
    participants: set,
    has_handlers: bool,
) -> str:
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
        task_name = task.get("name", "Unnamed task")
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
                diagram += (
                    f"    {executor}->>+{role_name_clean}: {role_action}: {role_name}\n"
                )
                diagram += f"    {role_name_clean}-->>-{executor}: Complete\n"

                # Check for notifications
                if "notify" in task and has_handlers:
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
                    diagram += (
                        f"    {executor}->>{executor}: {task_action}: {task_file}\n"
                    )
                elif isinstance(task_file, dict):
                    file_name = task_file.get("file", "unknown")
                    diagram += (
                        f"    {executor}->>{executor}: {task_action}: {file_name}\n"
                    )

                # Check for notifications
                if "notify" in task and has_handlers:
                    diagram += f"    {executor}->>Handlers: Notify\n"
                task_included = True
                break

        if task_included:
            continue

        # Regular task
        diagram += f"    {executor}->>{executor}: {task_name_short}\n"

        # Check for notifications
        if "notify" in task and has_handlers:
            diagram += f"    {executor}->>Handlers: Notify\n"

    return diagram
