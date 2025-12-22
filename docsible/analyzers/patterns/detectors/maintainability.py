"""Detectors for maintainability anti-patterns.

Identifies issues that make roles hard to maintain, test,
and understand over time.
"""

from typing import Any

from docsible.analyzers.patterns.base import BasePatternDetector
from docsible.analyzers.patterns.detectors.suggestions.maintanability_suggestion import Suggestion
from docsible.analyzers.patterns.models import (
    PatternCategory,
    SeverityLevel,
    SimplificationSuggestion,
)


class MaintainabilityDetector(BasePatternDetector):
    """Detects maintainability anti-patterns."""

    @property
    def pattern_category(self) -> PatternCategory:
        """Return maintainability category."""
        return PatternCategory.MAINTAINABILITY

    def detect(self, role_info: dict[str, Any]) -> list[SimplificationSuggestion]:
        """Detect all maintainability patterns.

        Args:
            role_info: Parsed role information

        Returns:
            List of suggestions for improving maintainability
        """
        suggestions: list[SimplificationSuggestion] = []

        suggestions.extend(self._detect_missing_idempotency(role_info))
        suggestions.extend(self._detect_monolithic_main_file(role_info))
        suggestions.extend(self._detect_magic_values(role_info))
        suggestions.extend(self._detect_missing_check_mode(role_info))
        suggestions.extend(self._detect_missing_failed_when(role_info))
        suggestions.extend(self._detect_variable_shadowing(role_info))

        return suggestions

    def _detect_missing_idempotency(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Detect tasks that may not be idempotent.

        shell/command/raw tasks without creates/removes/changed_when
        will always report 'changed' even if nothing actually changed.
        """
        suggestions: list[SimplificationSuggestion] = []

        # Modules that often lack idempotency
        risky_modules = ["shell", "command", "raw"]
        risky_tasks = []

        for task in self._flatten_tasks(role_info):
            module = task.get("module")

            if module in risky_modules:
                has_creates = self._has_attribute(task, "creates", "removes")
                has_changed_when = "changed_when" in task

                if not has_creates and not has_changed_when:
                    risky_tasks.append(task)

        if risky_tasks:
            suggestions.append(
                SimplificationSuggestion(
                    pattern="missing_idempotency",
                    category=self.pattern_category,
                    severity=SeverityLevel.WARNING,
                    description=f"Found {len(risky_tasks)} shell/command tasks without idempotency checks",
                    example=self._show_task_snippet(risky_tasks[:2]),
                    suggestion=Suggestion.missing_idempotency(),
                    affected_files=self._get_unique_files(risky_tasks),
                    impact="Ensures role can be run multiple times safely without unnecessary changes",
                    confidence=0.9,
                )
            )

        return suggestions

    def _detect_monolithic_main_file(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Detect main.yml files with too many tasks.

        Large main.yml files are hard to navigate and understand.
        Better to split into logical groups.
        """
        suggestions: list[SimplificationSuggestion] = []

        task_files = self._get_task_files(role_info)

        # Find main.yml
        main_file = next((f for f in task_files if f.get("file") == "main.yml"), None)

        if main_file:
            task_count = len(main_file.get("tasks", []))

            # Threshold: >30 tasks in main.yml
            if task_count > 30:
                suggestions.append(
                    SimplificationSuggestion(
                        pattern="monolithic_main_file",
                        category=self.pattern_category,
                        severity=SeverityLevel.WARNING,
                        description=f"main.yml contains {task_count} tasks (recommended: <30)",
                        example="",
                        suggestion=Suggestion.monolithic_main_file(),
                        affected_files=["tasks/main.yml"],
                        impact=f"Improves maintainability and navigation ({task_count} tasks → 4-5 focused files)",
                        confidence=0.95,
                    )
                )

        return suggestions

    def _detect_magic_values(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Detect repeated literal values that should be variables.

        Example: Path "/opt/myapp" hardcoded in 10 different tasks
        """
        suggestions: list[SimplificationSuggestion] = []
        from collections import defaultdict

        # Track string/number literals used across tasks
        literal_usage = defaultdict(list)

        for task in self._flatten_tasks(role_info):
            # Extract literals from task (simplified - would need deeper inspection)
            task_str = str(task)

            # Simple heuristic: find quoted strings that look like paths or config values
            import re

            quoted_strings = re.findall(r'"([^"]{10,})"', task_str)
            quoted_strings.extend(re.findall(r"'([^']{10,})'", task_str))

            for literal in quoted_strings:
                # Filter out Jinja2 templates
                if "{{" not in literal and "}}" not in literal:
                    # Filter out common non-config strings
                    if not any(
                        skip in literal.lower()
                        for skip in ["install", "ensure", "create", "configure"]
                    ):
                        literal_usage[literal].append(task.get("file", "unknown"))

        # Find literals used 3+ times
        magic_values = {
            literal: files
            for literal, files in literal_usage.items()
            if len(files) >= 3
        }

        if magic_values:
            # Show top offenders
            top_magic = sorted(
                magic_values.items(), key=lambda x: len(x[1]), reverse=True
            )[:3]

            example = "\n".join(
                [f"'{literal}' used {len(files)} times" for literal, files in top_magic]
            )

            suggestions.append(
                SimplificationSuggestion(
                    pattern="magic_values",
                    category=self.pattern_category,
                    severity=SeverityLevel.INFO,
                    description=f"Found {len(magic_values)} repeated literal values across tasks",
                    example=f"\n{example}\n",
                    suggestion=Suggestion.detect_magic_values(),
                    affected_files=list(
                        set([f for files in magic_values.values() for f in files])
                    ),
                    impact="Improves flexibility and reduces change burden",
                    confidence=0.7,
                )
            )

        return suggestions

    def _detect_missing_check_mode(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Find tasks that need check_mode directives.

        Tasks that register variables used later will fail in --check mode
        if they can't actually run.
        """
        suggestions: list[SimplificationSuggestion] = []

        tasks = self._flatten_tasks(role_info)
        problematic_tasks = []

        # Build dependency graph: which tasks register vars used by others
        for i, task in enumerate(tasks):
            if task.get("register"):
                registered_var = str(task.get("register"))

                # Check if this variable is used by later tasks
                for later_task in tasks[i + 1 :]:
                    task_str = str(later_task)
                    if registered_var in task_str:
                        # This is a dependency
                        module = task.get("module", "")
                        risky_modules = ["shell", "command", "stat"]

                        if module in risky_modules and "check_mode" not in task:
                            problematic_tasks.append(task)
                            break

        if problematic_tasks:
            suggestions.append(
                SimplificationSuggestion(
                    pattern="missing_check_mode",
                    category=self.pattern_category,
                    severity=SeverityLevel.INFO,
                    description=f"Found {len(problematic_tasks)} tasks that register variables but may fail in check mode",
                    example=self._show_task_snippet(problematic_tasks[:2]),
                    suggestion=Suggestion.missing_check_mode(),
                    affected_files=self._get_unique_files(problematic_tasks),
                    impact="Enables safe testing with --check flag",
                    confidence=0.75,
                )
            )

        return suggestions

    def _detect_missing_failed_when(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Find shell commands with pipes that may hide failures.

        Example: shell: cmd1 | cmd2
        If cmd1 fails but cmd2 succeeds, task reports success!
        """
        suggestions: list[SimplificationSuggestion] = []

        shell_tasks = self._get_tasks_by_module(role_info, "shell")
        command_tasks = self._get_tasks_by_module(role_info, "command")

        risky_tasks = []

        for task in shell_tasks + command_tasks:
            cmd = str(task.get("cmd", task.get("command", task.get("shell", ""))))

            # Check for pipes
            has_pipe = "|" in cmd
            has_failed_when = "failed_when" in task

            # Risky if has pipe but no explicit failure handling
            if has_pipe and not has_failed_when:
                risky_tasks.append(task)

        if risky_tasks:
            suggestions.append(
                SimplificationSuggestion(
                    pattern="missing_failed_when",
                    category=self.pattern_category,
                    severity=SeverityLevel.INFO,
                    description=f"Found {len(risky_tasks)} shell commands with pipes but no failure handling",
                    example=self._show_task_snippet(risky_tasks[:2]),
                    suggestion=Suggestion.missing_failed_when(),
                    affected_files=self._get_unique_files(risky_tasks),
                    impact="Prevents silent failures from being ignored",
                    confidence=0.8,
                )
            )

        return suggestions

    def _detect_variable_shadowing(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Detect variables defined in multiple locations.

        Variables in vars/ override defaults/, which can be confusing.
        """
        suggestions: list[SimplificationSuggestion] = []

        # Handle both dict and list formats
        defaults_raw = role_info.get("defaults", {})
        vars_raw = role_info.get("vars", {})

        # Convert to dict if list
        if isinstance(defaults_raw, list):
            defaults_dict = {}
            for item in defaults_raw:
                if isinstance(item, dict):
                    defaults_dict.update(item)
            defaults = set(defaults_dict.keys())
        else:
            defaults = set(defaults_raw.keys())

        if isinstance(vars_raw, list):
            vars_dict_temp = {}
            for item in vars_raw:
                if isinstance(item, dict):
                    vars_dict_temp.update(item)
            vars_dict = set(vars_dict_temp.keys())
        else:
            vars_dict = set(vars_raw.keys())

        # Find variables defined in both places
        shadowed = defaults.intersection(vars_dict)

        if shadowed:
            example_vars = list(shadowed)[:5]

            suggestions.append(
                SimplificationSuggestion(
                    pattern="variable_shadowing",
                    category=self.pattern_category,
                    severity=SeverityLevel.WARNING,
                    description=f"Found {len(shadowed)} variables defined in both defaults/ and vars/",
                    example=f"Shadowed variables: {', '.join(example_vars)}",
                    suggestion=Suggestion.variable_shadowing(),
                    affected_files=["defaults/main.yml", "vars/main.yml"],
                    impact="Eliminates confusion about which value will be used",
                    confidence=0.95,
                )
            )

        return suggestions
