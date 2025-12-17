"""
Mermaid sequence diagram generation for Ansible playbooks and roles.
Provides both high-level architecture and detailed execution flow visualizations.
"""

from .playbook import generate_mermaid_sequence_playbook_high_level
from .role import generate_mermaid_sequence_role_detailed
from .sanitization import sanitize_note_text, sanitize_participant_name

__all__ = [
    "sanitize_participant_name",
    "sanitize_note_text",
    "generate_mermaid_sequence_playbook_high_level",
    "generate_mermaid_sequence_role_detailed",
]
