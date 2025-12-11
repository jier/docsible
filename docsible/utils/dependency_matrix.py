"""
Dependency matrix generator for complex Ansible roles.

Generates task dependency tables showing relationships, triggers, and error handling.
Scales to any complexity level without visual clutter.
"""

import logging
import re
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TaskDependency:
    """Represents dependencies and relationships for a single task."""

    task_name: str
    module: str
    file: str
    requires: List[str]  # Variable/fact dependencies
    triggers: List[str]  # Handlers triggered
    error_handling: str  # Error handling strategy
    conditions: List[str]  # When conditions
    sets_facts: List[str]  # Variables/facts this task sets


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


def analyze_task_dependencies(
    tasks: List[Dict[str, Any]], task_file: str
) -> List[TaskDependency]:
    """
    Analyze task dependencies from role task data.

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

        # Extract variable dependencies from 'when' conditions
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

        # Extract variable dependencies from task args
        for key, value in task.items():
            if key not in ["name", "module", "when", "notify", "changed_when", "register"]:
                if isinstance(value, (str, dict, list)):
                    requires.update(extract_variable_references(str(value)))

        # Handler notifications
        notify_list = task.get("notify", [])
        if isinstance(notify_list, str):
            triggers = [notify_list]
        elif isinstance(notify_list, list):
            triggers = notify_list
        else:
            triggers = []

        # Error handling detection
        error_handling = "None"
        if "rescue" in task or "always" in task:
            if "rescue" in task and "always" in task:
                error_handling = "rescue + always"
            elif "rescue" in task:
                error_handling = "rescue"
            else:
                error_handling = "always"

        # Facts being set
        sets_facts = []
        if "register" in task:
            sets_facts.append(task["register"])
        if module == "set_fact" or module == "ansible.builtin.set_fact":
            # Extract fact names from set_fact args
            for key, value in task.items():
                if key not in ["name", "module", "when", "notify"]:
                    sets_facts.append(key)

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

    all_dependencies: List[TaskDependency] = []

    # Analyze all task files
    for task_file_info in task_files:
        file_name = task_file_info.get("file", "unknown")
        tasks = task_file_info.get("tasks", [])
        dependencies = analyze_task_dependencies(tasks, file_name)
        all_dependencies.extend(dependencies)

    if not all_dependencies:
        return None

    # Build markdown table
    lines = []

    if show_all_columns:
        lines.append(
            "| Task | File | Module | Requires | Triggers | Error Handling | Sets Facts |"
        )
        lines.append(
            "|------|------|--------|----------|----------|----------------|------------|"
        )

        for dep in all_dependencies:
            requires = ", ".join(dep.requires[:3]) if dep.requires else "-"
            if len(dep.requires) > 3:
                requires += f" (+{len(dep.requires) - 3} more)"

            triggers = ", ".join(dep.triggers) if dep.triggers else "-"
            sets_facts = ", ".join(dep.sets_facts) if dep.sets_facts else "-"

            lines.append(
                f"| {dep.task_name} | `{dep.file}` | `{dep.module}` | {requires} | {triggers} | {dep.error_handling} | {sets_facts} |"
            )
    else:
        # Essential columns only
        lines.append("| Task | File | Requires | Triggers |")
        lines.append("|------|------|----------|----------|")

        for dep in all_dependencies:
            requires = ", ".join(dep.requires[:2]) if dep.requires else "-"
            if len(dep.requires) > 2:
                requires += "..."

            triggers = ", ".join(dep.triggers) if dep.triggers else "-"

            lines.append(
                f"| {dep.task_name} | `{dep.file}` | {requires} | {triggers} |"
            )

    return "\n".join(lines)


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
