"""
Mermaid sequence diagram generation for Ansible roles.
Generates detailed diagrams showing role → tasks → handlers interaction.
"""

import logging
from typing import Dict, Any

from docsible.utils.mermaid import extract_task_name_from_module

from .sanitization import sanitize_participant_name, sanitize_note_text

logger = logging.getLogger(__name__)


def generate_mermaid_sequence_role_detailed(
    role_info: Dict[str, Any],
    include_handlers: bool = True,
    simplify_large: bool = False,
    max_lines: int = 20,
) -> str:
    """
    Generate detailed sequence diagram showing role → tasks → handlers interaction.

    Shows:
    - Task execution order (limited to first 10 tasks per file for clarity)
    - Remaining tasks count if more than 10 tasks exist per file
    - include_tasks/import_tasks as separate participants
    - include_role/import_role as separate participants
    - Handler notifications and execution
    - Block/rescue/always structures

    Args:
        role_info: Role information dict with tasks, handlers, meta
        include_handlers: Whether to include handler interactions
        simplify_large: If True, simplifies diagrams with more than max_lines.
                       Only set to True when --minimal or --simplify-diagrams flags are used.
        max_lines: Maximum lines before simplification kicks in

    Returns:
        Mermaid sequence diagram as string

    Note:
        The detailed diagram shows up to 10 individual tasks per file.
        If a file has more than 10 tasks, remaining tasks are indicated by count.
        Use simplify_large=True to show only file-level summaries without task details.
    """
    # First, generate the full diagram
    diagram = _generate_full_sequence_diagram(role_info, include_handlers)

    # Count lines in the diagram
    line_count = diagram.count("\n")

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
    for defaults_file in role_info.get("defaults", []):
        data = defaults_file.get("data", {})
        if "state" in data:
            state_info = data["state"]
            # Check choices
            choices = state_info.get("choices", "")
            if isinstance(choices, str) and (
                "present" in choices.lower() and "absent" in choices.lower()
            ):
                return True
            if (
                isinstance(choices, list)
                and any("present" in str(c).lower() for c in choices)
                and any("absent" in str(c).lower() for c in choices)
            ):
                return True
            # Check description
            description = state_info.get("description", "")
            if (
                "present" in str(description).lower()
                and "absent" in str(description).lower()
            ):
                return True

    # Check vars for state variable
    for vars_file in role_info.get("vars", []):
        data = vars_file.get("data", {})
        if "state" in data:
            state_info = data["state"]
            choices = state_info.get("choices", "")
            if isinstance(choices, str) and (
                "present" in choices.lower() and "absent" in choices.lower()
            ):
                return True
            if (
                isinstance(choices, list)
                and any("present" in str(c).lower() for c in choices)
                and any("absent" in str(c).lower() for c in choices)
            ):
                return True

    # Check tasks for state usage with present/absent
    for task_file_info in role_info.get("tasks", []):
        for task in task_file_info.get("tasks", []):
            if not isinstance(task, dict):
                continue
            # Check if task has state parameter with present/absent
            for key, value in task.items():
                if key == "state" and isinstance(value, str):
                    if value.lower() in ["present", "absent"]:
                        return True

    return False


def _generate_simplified_sequence_diagram(
    role_info: Dict[str, Any], include_handlers: bool
) -> str:
    """
    Generate simplified sequence diagram for large/complex roles.
    Shows only high-level structure: role → task files → handlers.
    """
    diagram = "sequenceDiagram\n"
    diagram += "    autonumber\n"

    role_name = role_info.get("name", "Role")
    role_participant = sanitize_participant_name(role_name)

    diagram += "    participant Playbook\n"
    diagram += f"    participant {role_participant}\n"

    # Add handlers if any
    handlers = []
    if include_handlers and role_info.get("handlers"):
        handlers = role_info["handlers"]
        diagram += "    participant Handlers\n"

    diagram += "\n"

    # Check for present/absent state support
    supports_states = _detect_state_support(role_info)

    if supports_states:
        # Show alternative flows for present/absent
        diagram += "    alt state: present\n"
        diagram += (
            f"    Playbook->>+{role_participant}: Execute role (ensure present)\n"
        )
        diagram += f"    activate {role_participant}\n"
    else:
        diagram += f"    Playbook->>+{role_participant}: Execute role\n"
        diagram += f"    activate {role_participant}\n"

    diagram += "\n"

    # Process tasks at file level only (no individual task details)
    tasks_data = role_info.get("tasks", [])

    for task_file_info in tasks_data:
        task_file = task_file_info.get("file", "main.yml")
        tasks = task_file_info.get("tasks", [])

        if not tasks:
            continue

        task_count = len(tasks)

        # Show task file with count
        diagram += f"    {role_participant}->>{role_participant}: Execute {task_file}\n"
        diagram += f"    Note right of {role_participant}: {task_count} tasks\n"

        # Check if any tasks notify handlers
        has_notify = any("notify" in task for task in tasks if isinstance(task, dict))
        if has_notify and include_handlers:
            diagram += f"    {role_participant}->>Handlers: Notify handlers\n"

        diagram += "\n"

    # Execute handlers if any were notified
    if include_handlers and handlers:
        diagram += (
            f"    Note over {role_participant},Handlers: Execute notified handlers\n"
        )
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
            task_file = task_file_info.get("file", "main.yml")
            tasks = task_file_info.get("tasks", [])
            if not tasks:
                continue
            task_count = len(tasks)
            diagram += (
                f"    {role_participant}->>{role_participant}: Execute {task_file}\n"
            )
            diagram += f"    Note right of {role_participant}: {task_count} tasks\n"

        diagram += f"    deactivate {role_participant}\n"
        diagram += f"    {role_participant}-->>-Playbook: Role complete\n"
        diagram += "    end\n"

    diagram += (
        f"\n    Note over Playbook: Simplified view - {len(tasks_data)} task files"
    )
    if supports_states:
        diagram += " (supports present/absent)"
    diagram += "\n"

    return diagram


def _generate_full_sequence_diagram(
    role_info: Dict[str, Any], include_handlers: bool
) -> str:
    """
    Generate detailed sequence diagram showing role → tasks → handlers interaction.

    Shows:
    - Task execution order (first 10 tasks shown individually per file)
    - Remaining tasks shown as count if more than 10 tasks exist
    - include_tasks/import_tasks as separate participants
    - include_role/import_role as separate participants
    - Handler notifications and execution
    - Block/rescue/always structures

    Args:
        role_info: Role information dict with tasks, handlers, meta
        include_handlers: Whether to include handler interactions

    Returns:
        Mermaid sequence diagram as string

    Note:
        To prevent overwhelming diagrams, only the first 10 tasks per file are shown
        in detail. If more than 10 tasks exist, a note indicates the remaining count.
    """
    diagram = "sequenceDiagram\n"
    diagram += "    autonumber\n"

    role_name = role_info.get("name", "Role")
    role_participant = sanitize_participant_name(role_name)

    diagram += "    participant Playbook\n"
    diagram += f"    participant {role_participant}\n"

    # Track all participants (tasks files, includes, roles, handlers)
    participants = {role_participant}

    # Collect handlers
    handlers = []
    if include_handlers and role_info.get("handlers"):
        handlers = role_info["handlers"]
        diagram += "    participant Handlers\n"
        participants.add("Handlers")

    diagram += "\n"
    diagram += f"    Playbook->>+{role_participant}: Execute role\n"
    diagram += f"    activate {role_participant}\n\n"

    # Process tasks
    tasks_data = role_info.get("tasks", [])

    for task_file_info in tasks_data:
        task_file = task_file_info.get("file", "main.yml")
        tasks = task_file_info.get("tasks", [])

        if not tasks:
            continue

        task_file_participant = sanitize_participant_name(
            f"Tasks_{task_file.replace('/', '_').replace('.', '_')}"
        )

        # Add task file as participant if not already there
        if task_file_participant not in participants:
            diagram += f"    participant {task_file_participant}\n"
            participants.add(task_file_participant)

        diagram += f"    Note over {role_participant},{task_file_participant}: File: {task_file}\n"
        diagram += f"    {role_participant}->>+{task_file_participant}: Load tasks\n\n"

        # Limit detailed task display to first 10 tasks
        max_detailed_tasks = 10
        total_tasks = len(tasks)
        tasks_to_show = tasks[:max_detailed_tasks]
        remaining_tasks = total_tasks - max_detailed_tasks

        # Process each task (up to max_detailed_tasks)
        for task_idx, task in enumerate(tasks_to_show):
            # Get task name - use extract_task_name_from_module for unnamed tasks
            if "name" not in task or not task["name"]:
                # Try to extract from original task data if available
                original_task = (
                    task_file_info.get("mermaid", [{}])[task_idx]
                    if task_idx < len(task_file_info.get("mermaid", []))
                    else task
                )
                task_name = extract_task_name_from_module(original_task, task_idx)
            else:
                task_name = task["name"]

            task_module = task.get("module", "unknown")

            # Sanitize task name for display
            task_display = sanitize_note_text(task_name, 40)

            # Handle include_tasks/import_tasks
            if task_module in [
                "include_tasks",
                "import_tasks",
                "ansible.builtin.include_tasks",
                "ansible.builtin.import_tasks",
            ]:
                include_file = task.get("file", "unknown")
                include_participant = sanitize_participant_name(
                    f"Include_{include_file.replace('/', '_').replace('.', '_')}"
                )

                if include_participant not in participants:
                    diagram += f"    participant {include_participant}\n"
                    participants.add(include_participant)

                diagram += f"    {task_file_participant}->>{include_participant}: {task_module}: {include_file}\n"
                diagram += f"    activate {include_participant}\n"
                diagram += f"    Note over {include_participant}: {task_display}\n"
                diagram += (
                    f"    {include_participant}-->>{task_file_participant}: Complete\n"
                )
                diagram += f"    deactivate {include_participant}\n"

            # Handle include_role/import_role
            elif task_module in [
                "include_role",
                "import_role",
                "ansible.builtin.include_role",
                "ansible.builtin.import_role",
            ]:
                included_role = task.get("name", task.get("role", "unknown"))
                role_include_participant = sanitize_participant_name(
                    f"Role_{included_role}"
                )

                if role_include_participant not in participants:
                    diagram += f"    participant {role_include_participant}\n"
                    participants.add(role_include_participant)

                diagram += f"    {task_file_participant}->>{role_include_participant}: {task_module}\n"
                diagram += f"    activate {role_include_participant}\n"
                diagram += f"    Note over {role_include_participant}: {task_display}\n"
                diagram += f"    {role_include_participant}-->>{task_file_participant}: Complete\n"
                diagram += f"    deactivate {role_include_participant}\n"

            # Handle block structures
            elif task_module == "block":
                diagram += (
                    f"    Note over {task_file_participant}: Block: {task_display}\n"
                )
                diagram += f"    {task_file_participant}->>{task_file_participant}: Execute block\n"

                # Check for rescue
                if "rescue" in task:
                    diagram += "    alt Block fails\n"
                    diagram += f"        {task_file_participant}->>{task_file_participant}: Execute rescue\n"
                    diagram += "    end\n"

                # Check for always
                if "always" in task:
                    diagram += f"    {task_file_participant}->>{task_file_participant}: Execute always\n"

            # Regular task
            else:
                diagram += f"    {task_file_participant}->>{task_file_participant}: {task_display}\n"
                diagram += f"    Note right of {task_file_participant}: {task_module}\n"

            # Check for handler notification
            if include_handlers and "notify" in task:
                notified = task["notify"]
                if isinstance(notified, list):
                    handler_names = ", ".join(notified)
                else:
                    handler_names = str(notified)

                diagram += f"    {task_file_participant}->>Handlers: Notify: {sanitize_note_text(handler_names, 30)}\n"

            diagram += "\n"

        # Show remaining tasks count if there are more than max_detailed_tasks
        if remaining_tasks > 0:
            diagram += f"    Note over {task_file_participant}: ... and {remaining_tasks} more tasks\n"
            diagram += "\n"

        diagram += (
            f"    {task_file_participant}-->>-{role_participant}: Tasks complete\n\n"
        )

    # Execute handlers if any were notified
    if include_handlers and handlers:
        diagram += (
            f"    Note over {role_participant},Handlers: Execute notified handlers\n"
        )
        diagram += f"    {role_participant}->>+Handlers: Flush handlers\n"

        for handler in handlers[:3]:  # Show first 3 handlers to avoid clutter
            handler_name = handler.get("name", "Handler")
            diagram += (
                f"    Handlers->>Handlers: {sanitize_note_text(handler_name, 40)}\n"
            )

        if len(handlers) > 3:
            diagram += (
                f"    Note over Handlers: ... and {len(handlers) - 3} more handlers\n"
            )

        diagram += f"    Handlers-->>-{role_participant}: Handlers complete\n\n"

    diagram += f"    deactivate {role_participant}\n"
    diagram += f"    {role_participant}-->>-Playbook: Role complete\n"

    return diagram
