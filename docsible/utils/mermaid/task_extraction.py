"""
Task name extraction utilities for Ansible tasks.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def extract_task_name_from_module(task: Dict[str, Any], task_index: int = 0) -> str:
    """Extract a meaningful task name from the task dict when 'name' is not provided.

    Uses the module name or action (include_role, import_tasks, etc.) to create
    a descriptive name instead of "Unnamed_task_X".

    Args:
        task: Task dictionary
        task_index: Index of the task (used as fallback)

    Returns:
        A descriptive task name

    Example:
        >>> task = {'apt': {'name': 'nginx'}}
        >>> extract_task_name_from_module(task, 0)
        'apt (task 0)'
    """
    # If task has a name, return it
    if "name" in task and task["name"]:
        return task["name"]

    # List of common task keys that aren't modules
    non_module_keys = {
        "name",
        "when",
        "tags",
        "notify",
        "register",
        "changed_when",
        "failed_when",
        "ignore_errors",
        "delegate_to",
        "run_once",
        "become",
        "become_user",
        "vars",
        "loop",
        "with_items",
        "until",
        "retries",
        "delay",
        "check_mode",
        "diff",
        "any_errors_fatal",
        "environment",
        "no_log",
        "throttle",
        "timeout",
        "block",
        "rescue",
        "always",
    }

    # Check for include/import tasks first (these are special)
    include_import_keys = [
        "include_tasks",
        "import_tasks",
        "include_role",
        "import_role",
        "ansible.builtin.include_tasks",
        "ansible.builtin.import_tasks",
        "ansible.builtin.include_role",
        "ansible.builtin.import_role",
        "include",
        "import_playbook",
    ]

    for key in include_import_keys:
        if key in task:
            value = task[key]
            # Extract the file/role name
            if isinstance(value, dict):
                target = (
                    value.get("name")
                    or value.get("file")
                    or value.get("role")
                    or str(value)
                )
            else:
                target = str(value)

            # Clean up the key name (remove ansible.builtin. prefix)
            clean_key = key.replace("ansible.builtin.", "")
            return f"{clean_key}: {target}"

    # Check for block (block has special structure)
    if "block" in task and isinstance(task.get("block"), list):
        return "block"

    # Find the module being used (first key that's not in non_module_keys)
    for key in task.keys():
        if key not in non_module_keys:
            # Found the module
            module_name = key.replace("ansible.builtin.", "")  # Clean up FQCN

            # Try to get a meaningful parameter from the module
            module_params = task[key]
            if isinstance(module_params, dict):
                # Common parameters that give context
                context_keys = [
                    "name",
                    "path",
                    "dest",
                    "src",
                    "pkg",
                    "package",
                    "service",
                    "key",
                    "repo",
                ]
                for context_key in context_keys:
                    if context_key in module_params:
                        context_value = str(module_params[context_key])[
                            :30
                        ]  # Limit length
                        return f"{module_name}: {context_value}"

            # Just return the module name
            return module_name

    # Fallback to unnamed with index
    return f"unnamed_task_{task_index}"
