"""
Phase and state detection for Ansible role workflows.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

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
class PhaseInfo:
    """Information about a detected phase."""

    phase: Phase
    tasks: list[dict[str, Any]]
    has_state_check: bool = False  # present/absent detection
    has_conditions: bool = False  # has 'when' conditions


# Phase detection patterns
PHASE_PATTERNS = {
    Phase.INSTALL: [
        r"\binstall",
        r"\bsetup\b",
        r"\binit",
        r"\bcreate\b",
        r"\bpackage\b",
        r"\bapt\b",
        r"\byum\b",
        r"\bdnf\b",
        r"\bdownload",
        r"\bfetch",
    ],
    Phase.CONFIGURE: [
        r"\bconfig",
        r"\bset\b",
        r"\bupdate\b",
        r"\bmodify\b",
        r"\btemplate\b",
        r"\bcopy\b",
        r"\bedit\b",
        r"\badjust\b",
        r"\bapply\b",
        r"\blineinfile\b",
        r"\bblockinfile\b",
    ],
    Phase.VALIDATE: [
        r"\bcheck",
        r"\bverif",
        r"\btest\b",
        r"\bensure\b",
        r"\bvalidat",
        r"\bassert\b",
        r"\bwait\b",
        r"\bstat\b",
        r"\bping\b",
        r"\bprobe\b",
    ],
    Phase.START: [
        r"\bstart",
        r"\benable\b",
        r"\blaunch",
        r"\brun\b",
        r"\bactivat",
        r"\binitiat",
    ],
    Phase.STOP: [
        r"\bstop",
        r"\bdisable\b",
        r"\bshutdown",
        r"\bterminat",
        r"\bdeactivat",
        r"\bhalt\b",
    ],
    Phase.CLEANUP: [
        r"\bclean",
        r"\bremove\b",
        r"\bdelete\b",
        r"\bpurge\b",
        r"\buninstall",
        r"\bdestroy\b",
        r"\bclear\b",
    ],
}

# Modules that typically check/set state
STATE_MODULES = {
    "package",
    "apt",
    "yum",
    "dnf",
    "pip",
    "npm",
    "gem",
    "service",
    "systemd",
    "file",
    "copy",
    "template",
    "user",
    "group",
    "mount",
    "lineinfile",
    "blockinfile",
    "ansible.builtin.package",
    "ansible.builtin.service",
    "ansible.builtin.file",
    "ansible.builtin.user",
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


def has_state_management(task: dict[str, Any]) -> bool:
    """
    Check if a task manages state (present/absent).

    Args:
        task: Task dictionary

    Returns:
        True if task uses state management modules
    """
    module = task.get("module", "")

    # Check if module is a state management module
    module_base = module.split(".")[-1]  # Handle ansible.builtin.service -> service
    if module_base in STATE_MODULES:
        return True

    # Check if task has 'state' parameter in common locations
    for key in ["args", "package", "service", "file", "user"]:
        if key in task and isinstance(task[key], dict):
            if "state" in task[key]:
                return True

    return False


def extract_condition(task: dict[str, Any]) -> str | None:
    """
    Extract the 'when' condition from a task.

    Args:
        task: Task dictionary

    Returns:
        Condition string or None
    """
    when_clause = task.get("when")

    if not when_clause:
        return None

    # Handle list of conditions
    if isinstance(when_clause, list):
        return " and ".join(str(c) for c in when_clause)

    return str(when_clause)


def analyze_phases(role_info: dict[str, Any]) -> list[PhaseInfo]:
    """
    Analyze role tasks and group them into phases.

    Args:
        role_info: Role information dictionary

    Returns:
        List of PhaseInfo objects
    """
    phases: dict[Phase, PhaseInfo] = {}

    tasks_data = role_info.get("tasks", [])

    for task_file in tasks_data:
        tasks = task_file.get("tasks", [])

        for task in tasks:
            task_name = task.get("name", "Unnamed task")

            # Detect phase
            phase = detect_phase_from_task_name(task_name)

            # Initialize phase info if not exists
            if phase not in phases:
                phases[phase] = PhaseInfo(
                    phase=phase, tasks=[], has_state_check=False, has_conditions=False
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
