"""Base classes for pattern detectors.

Provides common functionality and interface for all pattern detectors.
This follows the Template Method design pattern.
"""

from abc import ABC, abstractmethod
from typing import Any

from docsible.analyzers.patterns.models import PatternCategory, SimplificationSuggestion


class BasePatternDetector(ABC):
    """Abstract base class for all pattern detectors.

    Provides common utility methods and defines the interface that
    all detectors must implement.

    Design Pattern: Template Method
    - Concrete detectors implement `detect()` method
    - Base class provides helper utilities
    """

    @abstractmethod
    def detect(self, role_info: dict[str, Any]) -> list[SimplificationSuggestion]:
        """Detect patterns in the role.

        Args:
            role_info: Parsed role information dictionary containing:
                - tasks: List of task files with their tasks
                - vars: Role variables
                - defaults: Default variables
                - handlers: Handler definitions
                - meta: Role metadata

        Returns:
            List of simplification suggestions for patterns found
        """
        pass

    @property
    @abstractmethod
    def pattern_category(self) -> PatternCategory:
        """Return the category this detector handles."""
        pass

    def _flatten_tasks(self, role_info: dict[str, Any]) -> list[dict[str, Any]]:
        """Flatten all tasks from all task files into single list.

        Adds 'file' key to each task indicating source file.

        Args:
            role_info: Role information dictionary

        Returns:
            Flat list of all tasks with file metadata
        """
        tasks = []
        for task_file in role_info.get("tasks", []):
            file_name = task_file.get("file", "unknown")
            for task in task_file.get("tasks", []):
                task_with_file = task.copy()
                task_with_file["file"] = file_name
                tasks.append(task_with_file)
        return tasks

    def _get_task_files(self, role_info: dict[str, Any]) -> list[dict[str, Any]]:
        """Get list of task files from role info.

        Args:
            role_info: Role information dictionary

        Returns:
            List of task file dictionaries
        """
        return role_info.get("tasks", [])

    def _show_task_snippet(self, tasks: list[dict[str, Any]], limit: int = 2) -> str:
        """Generate example snippet from tasks.

        Args:
            tasks: List of task dictionaries
            limit: Maximum number of tasks to show

        Returns:
            YAML-like string representation
        """
        lines = []
        for task in tasks[:limit]:
            lines.append(f"- name: {task.get('name', 'unnamed')}")
            module = task.get("module", "unknown")
            lines.append(f"  {module}: ...")
        if len(tasks) > limit:
            lines.append(f"# ... and {len(tasks) - limit} more similar tasks")
        return "\n".join(lines)

    def _show_task(
        self, task: dict[str, Any], include_module_args: bool = False
    ) -> str:
        """Generate YAML-like representation of a single task.

        Args:
            task: Task dictionary
            include_module_args: Whether to show module arguments

        Returns:
            YAML-like string representation
        """
        lines = [f"- name: {task.get('name', 'unnamed')}"]
        module = task.get("module", "unknown")

        if include_module_args and "args" in task:
            lines.append(f"  {module}:")
            for key, value in task["args"].items():
                lines.append(f"    {key}: {value}")
        else:
            lines.append(f"  {module}: ...")

        return "\n".join(lines)

    def _count_tasks_by_module(self, role_info: dict[str, Any]) -> dict[str, int]:
        """Count how many times each module is used.

        Args:
            role_info: Role information dictionary

        Returns:
            Dictionary mapping module name to count
        """
        from collections import defaultdict

        counts = defaultdict(int)

        for task in self._flatten_tasks(role_info):
            module = task.get("module")
            if module:
                counts[module] += 1

        return dict(counts)

    def _get_tasks_by_module(
        self, role_info: dict[str, Any], module: str
    ) -> list[dict[str, Any]]:
        """Get all tasks using a specific module.

        Args:
            role_info: Role information dictionary
            module: Module name to filter by

        Returns:
            List of tasks using the specified module
        """
        return [
            task
            for task in self._flatten_tasks(role_info)
            if task.get("module") == module
        ]

    def _has_attribute(self, task: dict[str, Any], *attrs: str) -> bool:
        """Check if task has any of the specified attributes.

        Args:
            task: Task dictionary
            *attrs: Attribute names to check

        Returns:
            True if task has at least one of the attributes
        """
        return any(attr in task for attr in attrs)

    def _get_unique_files(self, tasks: list[dict[str, Any]]) -> list[str]:
        """Extract unique file names from tasks.

        Args:
            tasks: List of task dictionaries

        Returns:
            Sorted list of unique file names
        """
        files = {task.get("file") for task in tasks if task.get("file")}
        return sorted(files)
