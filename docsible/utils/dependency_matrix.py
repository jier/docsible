"""
Dependency matrix generator for complex Ansible roles.

Generates task dependency tables showing relationships, triggers, and error handling.
Scales to any complexity level without visual clutter.
"""

import logging
import re
from typing import Dict, Any, List, Set, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TaskDependency(BaseModel):
    """Represents dependencies and relationships for a single task."""

    task_name: str = Field(description="Name of the task")
    module: str = Field(description="Ansible module used by this task")
    file: str = Field(description="Task file location (e.g., main.yml)")
    requires: List[str] = Field(
        default_factory=list, description="Variable/fact dependencies"
    )
    triggers: List[str] = Field(
        default_factory=list, description="Handlers triggered by this task"
    )
    error_handling: str = Field(
        default="None", description="Error handling strategy (rescue/always/None)"
    )
    conditions: List[str] = Field(
        default_factory=list, description="When conditions for task execution"
    )
    sets_facts: List[str] = Field(
        default_factory=list, description="Variables/facts this task sets"
    )


# ============================================================================
# Variable Extraction Utilities
# ============================================================================


def extract_variable_references(text: str) -> Set[str]:
    """
    Extract Ansible variable references from text.

    Args:
        text: String that may contain Ansible variables

    Returns:
        Set of variable names referenced

    Example:
        >>> extract_variable_references("{{ foo }} and {{ bar.baz }}")
        {'foo', 'bar'}
    """
    if not text or not isinstance(text, str):
        return set()

    # Match {{ variable }} and {{ variable.property }}
    pattern = r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)"
    matches = re.findall(pattern, text)
    return set(matches)


# ============================================================================
# Task Analysis Helper Functions
# ============================================================================


def _extract_task_conditions(task: Dict[str, Any]) -> tuple[List[str], Set[str]]:
    """
    Extract when conditions and their variable dependencies from a task.

    Args:
        task: Task dictionary

    Returns:
        Tuple of (conditions list, set of required variables)
    """
    when_clause = task.get("when")
    conditions = []
    requires = set()

    if when_clause:
        if isinstance(when_clause, list):
            conditions = [str(c) for c in when_clause]
            for c in conditions:
                requires.update(extract_variable_references(c))
        else:
            conditions = [str(when_clause)]
            requires.update(extract_variable_references(str(when_clause)))

    return conditions, requires


def _extract_variable_dependencies(task: Dict[str, Any]) -> Set[str]:
    """
    Extract variable dependencies from task arguments.

    Args:
        task: Task dictionary

    Returns:
        Set of variable names referenced in task args
    """
    requires = set()
    excluded_keys = ["name", "module", "when", "notify", "changed_when", "register"]

    for key, value in task.items():
        if key not in excluded_keys:
            if isinstance(value, (str, dict, list)):
                requires.update(extract_variable_references(str(value)))

    return requires


def _extract_handler_triggers(task: Dict[str, Any]) -> List[str]:
    """
    Extract handler notification triggers from a task.

    Args:
        task: Task dictionary

    Returns:
        List of handler names triggered by this task
    """
    notify_list = task.get("notify", [])

    if isinstance(notify_list, str):
        return [notify_list]
    elif isinstance(notify_list, list):
        return notify_list
    else:
        return []


def _detect_error_handling(task: Dict[str, Any]) -> str:
    """
    Detect error handling strategy for a task.

    Args:
        task: Task dictionary

    Returns:
        Error handling strategy: "rescue", "always", "rescue + always", or "None"
    """
    has_rescue = "rescue" in task
    has_always = "always" in task

    if has_rescue and has_always:
        return "rescue + always"
    elif has_rescue:
        return "rescue"
    elif has_always:
        return "always"
    else:
        return "None"


def _extract_facts_set(task: Dict[str, Any]) -> List[str]:
    """
    Extract variables/facts that this task sets.

    Args:
        task: Task dictionary

    Returns:
        List of variable/fact names set by this task
    """
    sets_facts = []
    module = task.get("module", "")

    # Check for registered variables
    if "register" in task:
        sets_facts.append(task["register"])

    # Check for set_fact module
    if module in ["set_fact", "ansible.builtin.set_fact"]:
        excluded_keys = ["name", "module", "when", "notify"]
        for key in task.keys():
            if key not in excluded_keys:
                sets_facts.append(key)

    return sets_facts


# ============================================================================
# Core Dependency Analysis
# ============================================================================


def analyze_task_dependencies(
    tasks: List[Dict[str, Any]], task_file: str
) -> List[TaskDependency]:
    """
    Analyze task dependencies from role task data.

    This function orchestrates the extraction of various task attributes using
    specialized helper functions to build a complete dependency profile.

    Args:
        tasks: List of task dictionaries
        task_file: Name of the task file

    Returns:
        List of TaskDependency objects

    Example:
        >>> deps = analyze_task_dependencies(role_tasks, "main.yml")
        >>> print(deps[0].task_name)
        'Install packages'
    """
    dependencies = []

    for task in tasks:
        if not isinstance(task, dict):
            continue

        task_name = task.get("name", "*unnamed*")
        module = task.get("module", "unknown")

        # Extract all task attributes using helper functions
        conditions, condition_vars = _extract_task_conditions(task)
        arg_vars = _extract_variable_dependencies(task)
        triggers = _extract_handler_triggers(task)
        error_handling = _detect_error_handling(task)
        sets_facts = _extract_facts_set(task)

        # Combine all variable requirements
        requires = condition_vars | arg_vars

        dependencies.append(
            TaskDependency(
                task_name=task_name,
                module=module,
                file=task_file,
                requires=sorted(list(requires)),
                triggers=triggers,
                error_handling=error_handling,
                conditions=conditions,
                sets_facts=sets_facts,
            )
        )

    return dependencies


# ============================================================================
# Markdown Table Generation Helpers
# ============================================================================


def _collect_all_dependencies(role_info: Dict[str, Any]) -> List[TaskDependency]:
    """
    Collect dependencies from all task files in a role.

    Args:
        role_info: Role information dictionary with tasks

    Returns:
        List of all TaskDependency objects across all task files
    """
    all_dependencies: List[TaskDependency] = []
    task_files = role_info.get("tasks", [])

    for task_file_info in task_files:
        file_name = task_file_info.get("file", "unknown")
        tasks = task_file_info.get("tasks", [])
        dependencies = analyze_task_dependencies(tasks, file_name)
        all_dependencies.extend(dependencies)

    return all_dependencies


def _format_requires_list(requires: List[str], max_items: int = 3) -> str:
    """
    Format variable requirements list for table display.

    Args:
        requires: List of required variable names
        max_items: Maximum items to show before truncating

    Returns:
        Formatted string with truncation indicator if needed
    """
    if not requires:
        return "-"

    displayed = ", ".join(requires[:max_items])
    if len(requires) > max_items:
        displayed += f" (+{len(requires) - max_items} more)"

    return displayed


def _format_list_column(items: List[str]) -> str:
    """
    Format a list of items for table column display.

    Args:
        items: List of items to format

    Returns:
        Comma-separated string or "-" if empty
    """
    return ", ".join(items) if items else "-"


def _build_full_table(dependencies: List[TaskDependency]) -> List[str]:
    """
    Build complete dependency table with all columns.

    Args:
        dependencies: List of TaskDependency objects

    Returns:
        List of markdown table lines
    """
    lines = [
        "| Task | File | Module | Requires | Triggers | Error Handling | Sets Facts |",
        "|------|------|--------|----------|----------|----------------|------------|",
    ]

    for dep in dependencies:
        requires = _format_requires_list(dep.requires, max_items=3)
        triggers = _format_list_column(dep.triggers)
        sets_facts = _format_list_column(dep.sets_facts)

        lines.append(
            f"| {dep.task_name} | `{dep.file}` | `{dep.module}` | {requires} | {triggers} | {dep.error_handling} | {sets_facts} |"
        )

    return lines


def _build_essential_table(dependencies: List[TaskDependency]) -> List[str]:
    """
    Build simplified dependency table with essential columns only.

    Args:
        dependencies: List of TaskDependency objects

    Returns:
        List of markdown table lines
    """
    lines = [
        "| Task | File | Requires | Triggers |",
        "|------|------|----------|----------|",
    ]

    for dep in dependencies:
        requires = _format_requires_list(dep.requires, max_items=2)
        if len(dep.requires) > 2 and "+" not in requires:
            requires += "..."
        triggers = _format_list_column(dep.triggers)

        lines.append(f"| {dep.task_name} | `{dep.file}` | {requires} | {triggers} |")

    return lines


def generate_dependency_matrix_markdown(
    role_info: Dict[str, Any], show_all_columns: bool = True
) -> Optional[str]:
    """
    Generate markdown table showing task dependencies.

    Args:
        role_info: Role information dictionary with tasks
        show_all_columns: If True, show all columns; if False, only essential columns

    Returns:
        Markdown table as string, or None if no tasks

    Example:
        >>> table = generate_dependency_matrix_markdown(role_info)
        >>> print(table)
        | Task | File | Requires | Triggers | Error Handling |
        |------|------|----------|----------|----------------|
        | Install packages | main.yml | pkg_list | restart_service | rescue |
    """
    task_files = role_info.get("tasks", [])
    if not task_files:
        return None

    all_dependencies = _collect_all_dependencies(role_info)
    if not all_dependencies:
        return None

    # Build appropriate table based on column preference
    if show_all_columns:
        lines = _build_full_table(all_dependencies)
    else:
        lines = _build_essential_table(all_dependencies)

    return "\n".join(lines)


# ============================================================================
# Decision Logic & Statistics
# ============================================================================


def should_generate_dependency_matrix(
    role_info: Dict[str, Any], complexity_report: Any
) -> bool:
    """
    Determine if dependency matrix should be generated.

    Matrix is useful for:
    - Complex roles (20+ tasks)
    - Roles with many conditional tasks
    - Roles with error handling

    Args:
        role_info: Role information dictionary
        complexity_report: ComplexityReport object

    Returns:
        True if dependency matrix should be generated

    Example:
        >>> should_generate = should_generate_dependency_matrix(role_info, report)
        >>> if should_generate:
        ...     matrix = generate_dependency_matrix_markdown(role_info)
    """
    if not complexity_report:
        return False

    # Generate for complex roles
    if complexity_report.category.value == "complex":
        return True

    # Generate for medium roles with high conditional complexity
    if complexity_report.category.value == "medium":
        if complexity_report.metrics.conditional_percentage > 40:
            return True

    return False


def generate_dependency_summary(dependencies: List[TaskDependency]) -> Dict[str, Any]:
    """
    Generate summary statistics about task dependencies.

    Args:
        dependencies: List of TaskDependency objects

    Returns:
        Dictionary with summary statistics

    Example:
        >>> summary = generate_dependency_summary(dependencies)
        >>> print(f"Tasks with error handling: {summary['error_handling_count']}")
    """
    total_tasks = len(dependencies)
    tasks_with_requirements = sum(1 for d in dependencies if d.requires)
    tasks_with_triggers = sum(1 for d in dependencies if d.triggers)
    tasks_with_error_handling = sum(
        1 for d in dependencies if d.error_handling != "None"
    )
    tasks_setting_facts = sum(1 for d in dependencies if d.sets_facts)

    return {
        "total_tasks": total_tasks,
        "tasks_with_requirements": tasks_with_requirements,
        "tasks_with_triggers": tasks_with_triggers,
        "error_handling_count": tasks_with_error_handling,
        "tasks_setting_facts": tasks_setting_facts,
    }
