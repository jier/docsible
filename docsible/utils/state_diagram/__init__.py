"""
State transition diagram generator for Ansible roles.

Generates Mermaid state diagrams showing role workflow phases and state transitions.
"""

from .analyzer import (
    Phase,
    PhaseInfo,
    detect_phase_from_task_name,
    has_state_management,
    extract_condition,
    analyze_phases,
)
from .formatter import StateTransition, infer_transitions
from .generator import generate_state_diagram, should_generate_state_diagram

__all__ = [
    "Phase",
    "PhaseInfo",
    "StateTransition",
    "detect_phase_from_task_name",
    "has_state_management",
    "extract_condition",
    "analyze_phases",
    "infer_transitions",
    "generate_state_diagram",
    "should_generate_state_diagram",
]
