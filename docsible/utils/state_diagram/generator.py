"""
Main state diagram generation for Ansible roles.
"""

import logging
from typing import Dict, Any, Optional

from .analyzer import Phase, analyze_phases
from .formatter import infer_transitions

logger = logging.getLogger(__name__)


def generate_state_diagram(
    role_info: Dict[str, Any], role_name: Optional[str] = None
) -> Optional[str]:
    """
    Generate a Mermaid state transition diagram for a role.

    Args:
        role_info: Role information dictionary
        role_name: Optional role name for diagram title

    Returns:
        Mermaid state diagram as string, or None if insufficient data

    Example:
        >>> role_info = {...}
        >>> diagram = generate_state_diagram(role_info, "webserver")
        >>> print(diagram)
        stateDiagram-v2
            [*] --> Install
            Install --> Configure: when packages installed
            ...
    """
    # Analyze phases
    phases = analyze_phases(role_info)

    if not phases or len(phases) == 0:
        logger.warning("No phases detected in role")
        return None

    # If only one phase with few tasks, don't generate state diagram
    if len(phases) == 1 and len(phases[0].tasks) < 5:
        logger.info("Single phase with few tasks - state diagram not needed")
        return None

    # Infer transitions
    transitions = infer_transitions(phases)

    # Build Mermaid diagram
    lines = []

    # Add title if role name provided
    if role_name:
        lines.append(f"---")
        lines.append(f"title: {role_name} - State Transitions")
        lines.append(f"---")

    lines.append("stateDiagram-v2")

    # Determine entry and exit phases
    phase_set = {p.phase for p in phases}

    # Entry point: Install if exists, otherwise first phase
    if Phase.INSTALL in phase_set:
        entry_phase = Phase.INSTALL
    elif Phase.CONFIGURE in phase_set:
        entry_phase = Phase.CONFIGURE
    else:
        entry_phase = phases[0].phase

    # Exit point: Start if exists, otherwise Execute, otherwise last phase
    if Phase.START in phase_set:
        exit_phase = Phase.START
    elif Phase.EXECUTE in phase_set:
        exit_phase = Phase.EXECUTE
    else:
        exit_phase = phases[-1].phase

    # Add initial transition
    lines.append(f"    [*] --> {entry_phase.value.capitalize()}")

    # Add phase transitions
    for transition in transitions:
        from_state = transition.from_phase.value.capitalize()
        to_state = transition.to_phase.value.capitalize()

        if transition.condition:
            lines.append(f"    {from_state} --> {to_state}: {transition.condition}")
        else:
            lines.append(f"    {from_state} --> {to_state}")

    # Add notes for phases with state checks
    for phase_info in phases:
        if phase_info.has_state_check:
            phase_name = phase_info.phase.value.capitalize()
            task_count = len(phase_info.tasks)
            lines.append(
                f"    note right of {phase_name}: {task_count} tasks with state management"
            )

    # Add final transition if not cleanup
    if Phase.CLEANUP in phase_set:
        lines.append(f"    {Phase.CLEANUP.value.capitalize()} --> [*]")
    else:
        lines.append(f"    {exit_phase.value.capitalize()} --> [*]")

    return "\n".join(lines)


def should_generate_state_diagram(
    role_info: Dict[str, Any], complexity_category: str
) -> bool:
    """
    Determine if a state diagram should be generated for this role.

    Args:
        role_info: Role information dictionary
        complexity_category: Complexity category (SIMPLE, MEDIUM, COMPLEX)

    Returns:
        True if state diagram should be generated

    Decision logic:
        - SIMPLE roles: No (use sequence diagrams)
        - MEDIUM roles: Yes
        - COMPLEX roles: No (use architecture diagrams)
    """
    # Only generate for MEDIUM complexity roles
    if complexity_category.upper() != "MEDIUM":
        return False

    # Check if role has enough tasks to warrant state diagram
    tasks_data = role_info.get("tasks", [])
    total_tasks = sum(len(tf.get("tasks", [])) for tf in tasks_data)

    # Need at least 5 tasks to make a meaningful state diagram
    return total_tasks >= 5
