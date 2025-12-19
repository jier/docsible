"""Conditional complexity hotspot detection."""

import re
from typing import Any

from .models import ConditionalHotspot, FileComplexityDetail


def detect_conditional_hotspots(
    role_info: dict[str, Any], file_details: list[FileComplexityDetail]
) -> list[ConditionalHotspot]:
    """Identify files with concentrated conditional logic and the variables driving it.

    Args:
        role_info: Role information dictionary
        file_details: File complexity analysis results

    Returns:
        List of ConditionalHotspot objects

    Example:
        >>> hotspots = detect_conditional_hotspots(role_info, file_details)
        >>> for hotspot in hotspots:
        ...     print(f"{hotspot.file_path}: {hotspot.conditional_variable}")
    """
    hotspots = []

    # Focus on files with high conditional percentage
    conditional_files = [f for f in file_details if f.is_conditional_heavy]

    for file_detail in conditional_files:
        # Find the corresponding task file data
        task_file_info = next(
            (
                tf
                for tf in role_info.get("tasks", [])
                if tf.get("file") == file_detail.file_path
            ),
            None,
        )

        if not task_file_info:
            continue

        tasks = task_file_info.get("tasks", [])

        # Analyze conditional variables
        conditional_vars = _extract_conditional_variables(tasks)

        if conditional_vars:
            # Find most common conditional variable
            most_common = max(conditional_vars.items(), key=lambda x: x[1])
            var_name, usage_count = most_common

            # Count tasks affected by this variable
            affected_tasks = sum(
                1 for t in tasks if t.get("when") and var_name in str(t.get("when"))
            )

            # Generate suggestion
            suggestion = _generate_split_suggestion(var_name, file_detail.file_path)

            hotspots.append(
                ConditionalHotspot(
                    file_path=file_detail.file_path,
                    conditional_variable=var_name,
                    usage_count=usage_count,
                    affected_tasks=affected_tasks,
                    suggestion=suggestion,
                )
            )

    return hotspots


def _extract_conditional_variables(tasks: list[dict[str, Any]]) -> dict[str, int]:
    """Extract variables used in 'when' conditions and count their usage.

    Args:
        tasks: List of tasks

    Returns:
        Dictionary mapping variable names to usage count

    Example:
        >>> tasks = [
        ...     {"when": "ansible_os_family == 'Debian'"},
        ...     {"when": "ansible_os_family == 'RedHat'"}
        ... ]
        >>> _extract_conditional_variables(tasks)
        {'ansible_os_family': 2}
    """
    var_counter: dict[str, int] = {}

    # Common Ansible fact/variable patterns
    VAR_PATTERN = re.compile(r"([a-z_][a-z0-9_]*)")

    for task in tasks:
        when_clause = task.get("when")
        if not when_clause:
            continue

        # Convert to string (can be list or string)
        when_str = str(when_clause)

        # Extract variable names
        matches = VAR_PATTERN.findall(when_str)

        for var_name in matches:
            # Filter out common operators and keywords
            if var_name in ["and", "or", "not", "is", "in", "true", "false", "defined"]:
                continue

            var_counter[var_name] = var_counter.get(var_name, 0) + 1

    return var_counter


def _generate_split_suggestion(var_name: str, file_path: str) -> str:
    """Generate a suggestion for splitting based on conditional variable.

    Args:
        var_name: Variable name driving conditionals
        file_path: Original file path

    Returns:
        Suggested split strategy

    Example:
        >>> _generate_split_suggestion("ansible_os_family", "tasks/main.yml")
        'Split into tasks/debian.yml and tasks/redhat.yml based on OS family'
    """
    # Common patterns
    if "os_family" in var_name or "distribution" in var_name:
        return "Split into tasks/debian.yml and tasks/redhat.yml based on OS family"
    elif "environment" in var_name or "env" in var_name:
        return "Split into tasks/production.yml and tasks/staging.yml by environment"
    elif "mode" in var_name or "strategy" in var_name:
        return f"Split by {var_name} into separate task files"
    else:
        base_name = file_path.replace("tasks/", "").replace(".yml", "")
        return f"Extract conditional logic into tasks/{base_name}_{{value}}.yml files"
