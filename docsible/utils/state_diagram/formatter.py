"""
State transition inference and formatting for Mermaid diagrams.
"""

from dataclasses import dataclass

from .analyzer import Phase, PhaseInfo


@dataclass
class StateTransition:
    """Represents a state transition in the role workflow."""

    from_phase: Phase
    to_phase: Phase
    condition: str | None = None  # from 'when' clause
    description: str | None = None


def infer_transitions(phases: list[PhaseInfo]) -> list[StateTransition]:
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
            actual_condition = (
                condition if to_phase_info and to_phase_info.has_conditions else None
            )

            transitions.append(
                StateTransition(
                    from_phase=from_phase, to_phase=to_phase, condition=actual_condition
                )
            )

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
                        transitions.append(
                            StateTransition(from_phase=phase, to_phase=Phase.EXECUTE)
                        )

    return transitions
