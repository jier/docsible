"""Detectors for duplication anti-patterns.

Identifies tasks, configurations, or logic that is repeated
unnecessarily and could be consolidated.
"""

from collections import defaultdict
from typing import Any

from docsible.analyzers.patterns.base import BasePatternDetector
from docsible.analyzers.patterns.models import (
    PatternCategory,
    SeverityLevel,
    SimplificationSuggestion,
)
from docsible.analyzers.shared.module_taxonomy import (
    FILE_MODULES,
    PACKAGE_MODULES,
    SERVICE_MODULES,
)


class DuplicationDetector(BasePatternDetector):
    """Detects duplicated tasks and repetitive patterns."""

    @property
    def pattern_category(self) -> PatternCategory:
        """Return duplication category."""
        return PatternCategory.DUPLICATION

    def detect(self, role_info: dict[str, Any]) -> list[SimplificationSuggestion]:
        """Detect all duplication patterns.

        Args:
            role_info: Parsed role information

        Returns:
            List of suggestions for reducing duplication
        """
        suggestions: list[SimplificationSuggestion] = []

        # Run all duplication checks
        suggestions.extend(self._detect_repeated_package_installs(role_info))
        suggestions.extend(self._detect_repeated_service_operations(role_info))
        suggestions.extend(self._detect_repeated_file_operations(role_info))
        suggestions.extend(self._detect_similar_tasks(role_info))

        return suggestions

    def _detect_repeated_package_installs(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Find roles with many individual package installation tasks.

        Example anti-pattern:
            - name: Install nginx
              apt: name=nginx
            - name: Install php
              apt: name=php
            # ... 10 more separate tasks

        Better approach:
            - name: Install packages
              apt:
                name: "{{ item }}"
              loop: [nginx, php, ...]
        """
        suggestions: list[SimplificationSuggestion] = []

        # Short family names used for suggestion text and per-family grouping.
        # Membership is checked against PACKAGE_MODULES from the shared taxonomy.
        package_module_families = ["apt", "yum", "dnf", "package", "pip", "npm"]

        for pkg_module in package_module_families:
            # Match this family: all entries in the shared taxonomy that contain
            # the short name (covers both "apt" and "ansible.builtin.apt" etc.)
            family_modules = {m for m in PACKAGE_MODULES if pkg_module in m}
            all_tasks = self._flatten_tasks(role_info)
            tasks = [t for t in all_tasks if t.get("module") in family_modules]

            # Threshold: 5+ separate package tasks suggests opportunity
            if len(tasks) > 5:
                suggestions.append(
                    SimplificationSuggestion(
                        pattern="repeated_package_install",
                        category=self.pattern_category,
                        severity=SeverityLevel.WARNING,
                        description=f"Found {len(tasks)} separate {pkg_module} tasks",
                        example=self._show_task_snippet(tasks[:3]),
                        suggestion=(
                            f"Combine into single task with loop:\n\n"
                            f"```yaml\n"
                            f"- name: Install packages\n"
                            f"  {pkg_module}:\n"
                            f'    name: "{{{{ item }}}}"\n'
                            f"  loop:\n"
                            f"    - package1\n"
                            f"    - package2\n"
                            f"    - package3\n"
                            f"```\n\n"
                            f"Or use list directly:\n\n"
                            f"```yaml\n"
                            f"- name: Install packages\n"
                            f"  {pkg_module}:\n"
                            f"    name:\n"
                            f"      - package1\n"
                            f"      - package2\n"
                            f"```"
                        ),
                        affected_files=self._get_unique_files(tasks),
                        impact=f"Reduces {len(tasks)} tasks to 1 task (-{len(tasks) - 1} tasks)",
                        confidence=0.9,
                    )
                )

        return suggestions

    def _detect_repeated_service_operations(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Find repeated service start/stop/restart operations.

        Example: Starting 5 different services in 5 separate tasks
        """
        suggestions: list[SimplificationSuggestion] = []

        all_tasks = self._flatten_tasks(role_info)
        service_tasks = [t for t in all_tasks if t.get("module") in SERVICE_MODULES]
        systemd_tasks: list[dict] = []  # Already included in SERVICE_MODULES; kept for clarity

        all_service_tasks = service_tasks + systemd_tasks

        if len(all_service_tasks) > 5:
            # Group by state (started, restarted, etc.)
            by_state = defaultdict(list)
            for task in all_service_tasks:
                # Try to extract state from task args or name
                state = task.get("args", {}).get("state", "unknown")
                by_state[state].append(task)

            # Check each state group
            for state, tasks in by_state.items():
                if len(tasks) > 3:
                    suggestions.append(
                        SimplificationSuggestion(
                            pattern="repeated_service_operations",
                            category=self.pattern_category,
                            severity=SeverityLevel.INFO,
                            description=f"Found {len(tasks)} separate service tasks with state '{state}'",
                            example=self._show_task_snippet(tasks[:2]),
                            suggestion=(
                                f"Consider combining with loop:\n\n"
                                f"```yaml\n"
                                f"- name: Ensure services are {state}\n"
                                f"  service:\n"
                                f'    name: "{{{{ item }}}}"\n'
                                f"    state: {state}\n"
                                f"  loop:\n"
                                f"    - service1\n"
                                f"    - service2\n"
                                f"```"
                            ),
                            affected_files=self._get_unique_files(tasks),
                            impact=f"Reduces {len(tasks)} tasks to 1 task",
                            confidence=0.85,
                        )
                    )

        return suggestions

    def _detect_repeated_file_operations(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Find repeated file/directory creation or copying.

        Example: Creating many directories individually
        """
        suggestions: list[SimplificationSuggestion] = []

        # Only match the "file" module family for directory/file operations
        file_family_modules = {m for m in FILE_MODULES if "file" in m}
        all_tasks = self._flatten_tasks(role_info)
        file_tasks = [t for t in all_tasks if t.get("module") in file_family_modules]

        if len(file_tasks) > 5:
            # Group by state (directory, file, etc.)
            by_state = defaultdict(list)
            for task in file_tasks:
                state = task.get("args", {}).get("state", "unknown")
                by_state[state].append(task)

            # Check directory creation specifically
            if len(by_state.get("directory", [])) > 4:
                dir_tasks = by_state["directory"]
                suggestions.append(
                    SimplificationSuggestion(
                        pattern="repeated_directory_creation",
                        category=self.pattern_category,
                        severity=SeverityLevel.INFO,
                        description=f"Found {len(dir_tasks)} separate directory creation tasks",
                        example=self._show_task_snippet(dir_tasks[:2]),
                        suggestion=(
                            "Combine into single task with loop:\n\n"
                            "```yaml\n"
                            "- name: Create directories\n"
                            "  file:\n"
                            '    path: "{{ item }}"\n'
                            "    state: directory\n"
                            "    mode: '0755'\n"
                            "  loop:\n"
                            "    - /path/to/dir1\n"
                            "    - /path/to/dir2\n"
                            "```"
                        ),
                        affected_files=self._get_unique_files(dir_tasks),
                        impact=f"Reduces {len(dir_tasks)} tasks to 1 task",
                        confidence=0.9,
                    )
                )

        return suggestions

    def _detect_similar_tasks(self, role_info: dict[str, Any]) -> list[SimplificationSuggestion]:
        """Detect tasks with similar names suggesting duplication.

        Example: Tasks named "Configure X", "Configure Y", "Configure Z"
        might indicate a pattern that could be abstracted.
        """
        suggestions: list[SimplificationSuggestion] = []
        tasks = self._flatten_tasks(role_info)

        # Group tasks by common name prefixes
        prefix_groups = defaultdict(list)
        for task in tasks:
            name = task.get("name", "")
            # Extract first two words as prefix
            words = name.split()
            if len(words) >= 2:
                prefix = " ".join(words[:2])
                prefix_groups[prefix].append(task)

        # Find prefixes with many tasks
        for prefix, grouped_tasks in prefix_groups.items():
            if len(grouped_tasks) > 5:
                suggestions.append(
                    SimplificationSuggestion(
                        pattern="similar_task_names",
                        category=self.pattern_category,
                        severity=SeverityLevel.INFO,
                        description=f"Found {len(grouped_tasks)} tasks starting with '{prefix}...'",
                        example=self._show_task_snippet(grouped_tasks[:3]),
                        suggestion=(
                            "Consider abstracting pattern into reusable structure:\n\n"
                            "1. Use a loop with task data\n"
                            "2. Extract to separate included task file\n"
                            "3. Create custom module if logic is complex"
                        ),
                        affected_files=self._get_unique_files(grouped_tasks),
                        impact="Improves maintainability and reduces code duplication",
                        confidence=0.7,
                    )
                )

        return suggestions
