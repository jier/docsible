"""
Mermaid diagram generation utilities for Ansible.
"""

from .core import (
    break_text,
    sanitize_for_condition,
    sanitize_for_mermaid_id,
    sanitize_for_title,
)
from .formatting import (
    generate_mermaid_playbook,
    generate_mermaid_role_tasks_per_file,
    process_tasks,
)
from .task_extraction import extract_task_name_from_module

__all__ = [
    "extract_task_name_from_module",
    "sanitize_for_mermaid_id",
    "break_text",
    "sanitize_for_title",
    "sanitize_for_condition",
    "process_tasks",
    "generate_mermaid_playbook",
    "generate_mermaid_role_tasks_per_file",
]
