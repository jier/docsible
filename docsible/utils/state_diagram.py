"""
State transition diagram generator for Ansible roles.

Generates Mermaid state diagrams showing role workflow phases and state transitions.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Phase(str, Enum):
    """Role execution phases detected from task names."""
    INSTALL = "install"
    CONFIGURE = "configure"
    VALIDATE = "validate"
    START = "start"
    STOP = "stop"
    CLEANUP = "cleanup"
    EXECUTE = "execute"  # Default/generic phase


@dataclass
class StateTransition:
    """Represents a state transition in the role workflow."""
    from_phase: Phase
    to_phase: Phase
    condition: Optional[str] = None  # from 'when' clause
    description: Optional[str] = None


@dataclass
class PhaseInfo:
    """Information about a detected phase."""
    phase: Phase
    tasks: List[Dict[str, Any]]
    has_state_check: bool = False  # present/absent detection
    has_conditions: bool = False  # has 'when' conditions


# Phase detection patterns
PHASE_PATTERNS = {
    Phase.INSTALL: [
        r'\binstall', r'\bsetup\b', r'\binit', r'\bcreate\b',
        r'\bpackage\b', r'\bapt\b', r'\byum\b', r'\bdnf\b',
        r'\bdownload', r'\bfetch'
    ],
    Phase.CONFIGURE: [
        r'\bconfig', r'\bset\b', r'\bupdate\b', r'\bmodify\b',
        r'\btemplate\b', r'\bcopy\b', r'\bedit\b', r'\badjust\b',
        r'\bapply\b', r'\blineinfile\b', r'\bblockinfile\b'
    ],
    Phase.VALIDATE: [
        r'\bcheck', r'\bverif', r'\btest\b', r'\bensure\b',
        r'\bvalidat', r'\bassert\b', r'\bwait\b', r'\bstat\b',
        r'\bping\b', r'\bprobe\b'
    ],
    Phase.START: [
        r'\bstart', r'\benable\b', r'\blaunch', r'\brun\b',
        r'\bactivat', r'\binitiat'
    ],
    Phase.STOP: [
        r'\bstop', r'\bdisable\b', r'\bshutdown', r'\bterminat',
        r'\bdeactivat', r'\bhalt\b'
    ],
    Phase.CLEANUP: [
        r'\bclean', r'\bremove\b', r'\bdelete\b', r'\bpurge\b',
        r'\buninstall', r'\bdestroy\b', r'\bclear\b'
    ],
}

# Modules that typically check/set state
STATE_MODULES = {
    'package', 'apt', 'yum', 'dnf', 'pip', 'npm', 'gem',
    'service', 'systemd', 'file', 'copy', 'template',
    'user', 'group', 'mount', 'lineinfile', 'blockinfile',
    'ansible.builtin.package', 'ansible.builtin.service',
    'ansible.builtin.file', 'ansible.builtin.user',
}


def detect_phase_from_task_name(task_name: str) -> Phase:
    """
    Detect the phase from a task name using pattern matching.

    Args:
        task_name: Task name to analyze

    Returns:
        Detected Phase enum value

    Example:
        >>> detect_phase_from_task_name("Install nginx package")
        Phase.INSTALL
        >>> detect_phase_from_task_name("Configure web server")
        Phase.CONFIGURE
    """
    task_name_lower = task_name.lower()

    # Check each phase's patterns
    for phase, patterns in PHASE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, task_name_lower):
                return phase

    return Phase.EXECUTE


def has_state_management(task: Dict[str, Any]) -> bool:
    """
    Check if a task manages state (present/absent).

    Args:
        task: Task dictionary

    Returns:
        True if task uses state management modules
    """
    module = task.get('module', '')

    # Check if module is a state management module
    module_base = module.split('.')[-1]  # Handle ansible.builtin.service -> service
    if module_base in STATE_MODULES:
        return True

    # Check if task has 'state' parameter in common locations
    for key in ['args', 'package', 'service', 'file', 'user']:
        if key in task and isinstance(task[key], dict):
            if 'state' in task[key]:
                return True

    return False


def extract_condition(task: Dict[str, Any]) -> Optional[str]:
    """
    Extract the 'when' condition from a task.

    Args:
        task: Task dictionary

    Returns:
        Condition string or None
    """
    when_clause = task.get('when')

    if not when_clause:
        return None

    # Handle list of conditions
    if isinstance(when_clause, list):
        return ' and '.join(str(c) for c in when_clause)

    return str(when_clause)


def analyze_phases(role_info: Dict[str, Any]) -> List[PhaseInfo]:
    """
    Analyze role tasks and group them into phases.

    Args:
        role_info: Role information dictionary

    Returns:
        List of PhaseInfo objects
    """
    phases: Dict[Phase, PhaseInfo] = {}

    tasks_data = role_info.get('tasks', [])

    for task_file in tasks_data:
        tasks = task_file.get('tasks', [])

        for task in tasks:
            task_name = task.get('name', 'Unnamed task')

            # Detect phase
            phase = detect_phase_from_task_name(task_name)

            # Initialize phase info if not exists
            if phase not in phases:
                phases[phase] = PhaseInfo(
                    phase=phase,
                    tasks=[],
                    has_state_check=False,
                    has_conditions=False
                )

            # Add task to phase
            phases[phase].tasks.append(task)

            # Check for state management
            if has_state_management(task):
                phases[phase].has_state_check = True

            # Check for conditions
            if extract_condition(task):
                phases[phase].has_conditions = True

    return list(phases.values())


def infer_transitions(phases: List[PhaseInfo]) -> List[StateTransition]:
    """
    Infer state transitions between phases.

    Args:
        phases: List of PhaseInfo objects

    Returns:
        List of StateTransition objects

    Logic:
        - Standard workflow: Install -> Configure -> Validate -> Start
        - Cleanup is terminal
        - Stop comes before Cleanup
        - Execute can transition to any phase
    """
    transitions = []

    # Create a set of available phases
    available_phases = {p.phase for p in phases}

    # Define standard transition flow
    standard_flow = [
        (Phase.INSTALL, Phase.CONFIGURE, "when packages installed"),
        (Phase.CONFIGURE, Phase.VALIDATE, "when configuration applied"),
        (Phase.VALIDATE, Phase.START, "when validation passes"),
        (Phase.START, Phase.EXECUTE, "when service started"),
        (Phase.STOP, Phase.CLEANUP, "when stopped"),
    ]

    # Add standard transitions if both phases exist
    for from_phase, to_phase, condition in standard_flow:
        if from_phase in available_phases and to_phase in available_phases:
            # Check if the 'to' phase has conditions
            to_phase_info = next((p for p in phases if p.phase == to_phase), None)
            actual_condition = condition if to_phase_info and to_phase_info.has_conditions else None

            transitions.append(StateTransition(
                from_phase=from_phase,
                to_phase=to_phase,
                condition=actual_condition
            ))

    # Handle EXECUTE phase - it can be entry point or follow other phases
    if Phase.EXECUTE in available_phases:
        # If no other phases, EXECUTE is the only phase
        if len(available_phases) == 1:
            pass  # Just the execute phase, no transitions needed
        else:
            # Add transitions from other phases to EXECUTE if they exist
            for phase in available_phases:
                if phase != Phase.EXECUTE and phase not in [Phase.CLEANUP, Phase.STOP]:
                    # Check if there's already a transition from this phase
                    has_transition = any(t.from_phase == phase for t in transitions)
                    if not has_transition:
                        transitions.append(StateTransition(
                            from_phase=phase,
                            to_phase=Phase.EXECUTE
                        ))

    return transitions


def generate_state_diagram(role_info: Dict[str, Any], role_name: Optional[str] = None) -> Optional[str]:
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
            lines.append(f"    note right of {phase_name}: {task_count} tasks with state management")

    # Add final transition if not cleanup
    if Phase.CLEANUP in phase_set:
        lines.append(f"    {Phase.CLEANUP.value.capitalize()} --> [*]")
    else:
        lines.append(f"    {exit_phase.value.capitalize()} --> [*]")

    return '\n'.join(lines)


def should_generate_state_diagram(role_info: Dict[str, Any], complexity_category: str) -> bool:
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
    tasks_data = role_info.get('tasks', [])
    total_tasks = sum(len(tf.get('tasks', [])) for tf in tasks_data)

    # Need at least 5 tasks to make a meaningful state diagram
    return total_tasks >= 5
