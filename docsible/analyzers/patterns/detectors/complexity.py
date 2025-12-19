"""Detectors for complexity anti-patterns.

Identifies overly complex logic, conditionals, and control flow
that make roles hard to understand and maintain.
"""

from typing import Any

from docsible.analyzers.patterns.base import BasePatternDetector
from docsible.analyzers.patterns.detectors.suggestions.complexity_suggestion import Suggestion
from docsible.analyzers.patterns.models import (
    PatternCategory,
    SeverityLevel,
    SimplificationSuggestion,
)


class ComplexityDetector(BasePatternDetector):
    """Detects complexity anti-patterns."""

    _CONFIDENCE_LEVEL_INCLUDE_CHAINS = 0.9
    _CONFIDENCE_LEVEL_COMPLEX_CONDITIONALS = 0.85
    _CONFIDENCE_LEVEL_EXCESSIVE_SET_FACTS = 0.75
    _THRESHOLD_LOW = 2
    _THRESHOLD_MEDIUM = 3
    _THRESHOLD_HIGH = 5

    @property
    def pattern_category(self) -> PatternCategory:
        """Return complexity category."""
        return PatternCategory.COMPLEXITY

    def detect(self, role_info: dict[str, Any]) -> list[SimplificationSuggestion]:
        """Detect all complexity patterns.

        Args:
            role_info: Parsed role information

        Returns:
            List of suggestions for reducing complexity
        """
        suggestions: list[SimplificationSuggestion] = []

        suggestions.extend(self._detect_complex_conditionals(role_info))
        suggestions.extend(self._detect_deep_include_chains(role_info))
        suggestions.extend(self._detect_excessive_set_fact(role_info))

        return suggestions

    def _detect_complex_conditionals(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Find overly complex 'when' conditions.

        Example anti-pattern:
            when: (ansible_os_family == "Debian" and ansible_distribution_major_version >= "18")
                  or (ansible_os_family == "RedHat" and ansible_distribution_major_version >= "7")
                  or custom_flag is defined and custom_flag == true

        Better:
            Set intermediate facts or split into separate task files
        """
        suggestions: list[SimplificationSuggestion] = []

        for task_file in self._get_task_files(role_info):
            file_name = task_file.get("file", "unknown")

            for task in task_file.get("tasks", []):
                when = task.get("when")
                if not when:
                    continue

                # Convert to string for analysis
                when_str = str(when) if not isinstance(when, list) else " and ".join(map(str, when))

                # Count boolean operators
                or_count = when_str.lower().count(" or ")
                and_count = when_str.lower().count(" and ")
                total_operators = or_count + and_count

                # Detect complex conditionals
                # Threshold: More than _THRESHOLD_LOW ORs or more than _THRESHOLD_MEDIUM AND _THRESHOLD_HIGH
                is_complex = (
                    or_count > self._THRESHOLD_LOW
                    or and_count > self._THRESHOLD_MEDIUM
                    or total_operators > self._THRESHOLD_HIGH
                )

                if is_complex:
                    suggestions.append(
                        SimplificationSuggestion(
                            pattern="complex_conditional",
                            category=self.pattern_category,
                            severity=SeverityLevel.INFO,
                            description=f"Complex conditional in task '{task.get('name', 'unnamed')}' ({total_operators} operators)",
                            example=f"when: {when_str[:150]}..."
                            if len(when_str) > 150
                            else f"when: {when_str}",
                            suggestion=Suggestion.complex_conditionals(),
                            affected_files=[file_name],
                            impact="Improves readability and testability",
                            confidence=self._CONFIDENCE_LEVEL_COMPLEX_CONDITIONALS,
                        )
                    )

        return suggestions

    def _detect_deep_include_chains(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Detect deeply nested include_tasks/import_tasks chains.

        Example anti-pattern:
            main.yml → setup.yml → prereqs.yml → install_deps.yml (4 levels)

        Better:
            Flatten to 2-3 levels maximum
        """
        suggestions: list[SimplificationSuggestion] = []

        # Build include graph
        include_graph = {}
        for task_file in self._get_task_files(role_info):
            file_name = task_file.get("file", "unknown")
            includes = []

            for task in task_file.get("tasks", []):
                module = task.get("module", "")
                if module in [
                    "include_tasks",
                    "import_tasks",
                    "include_role",
                    "import_role",
                ]:
                    # Try to extract included file
                    included = task.get("file") or task.get("name", "").split()[-1]
                    includes.append(included)

            include_graph[file_name] = includes

        # Check depth starting from main.yml
        if "main.yml" in include_graph:
            depth = self._calculate_max_include_depth(include_graph, "main.yml", set())

            if depth > 3:
                # Build chain representation
                chain_example = " → ".join(list(include_graph.keys())[:depth])

                suggestions.append(
                    SimplificationSuggestion(
                        pattern="deep_include_chain",
                        category=self.pattern_category,
                        severity=SeverityLevel.WARNING,
                        description=f"Include chain depth is {depth} levels (recommended: ≤3)",
                        example=f"Chain example: {chain_example}",
                        suggestion=Suggestion.deep_include_chains(),
                        affected_files=list(include_graph.keys()),
                        impact="Easier debugging and flow understanding",
                        confidence=self._CONFIDENCE_LEVEL_INCLUDE_CHAINS,
                    )
                )

        return suggestions

    def _calculate_max_include_depth(
        self, include_graph: dict[str, list[str]], file_name: str, visited: set
    ) -> int:
        """Calculate maximum include depth from a file using DFS.

        Args:
            include_graph: Map of file names to their included files
            file_name: Starting file to calculate depth from
            visited: Set of already-visited files (for cycle detection)

        Returns:
            Maximum depth of include chain from this file
        """
        if file_name in visited:
            return 0  # Cycle detected, stop
        if file_name not in include_graph:
            return 1

        visited.add(file_name)
        max_child_depth = 0

        for included in include_graph[file_name]:
            depth = self._calculate_max_include_depth(include_graph, included, visited.copy())
            max_child_depth = max(max_child_depth, depth)

        return 1 + max_child_depth

    def _detect_excessive_set_fact(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Detect overuse of set_fact tasks.

        Example anti-pattern:
            20% or more of tasks are just variable assignments

        Better:
            Use vars: at play/task level, or role defaults
        """
        suggestions: list[SimplificationSuggestion] = []

        tasks = self._flatten_tasks(role_info)
        if not tasks:
            return suggestions

        set_fact_tasks = [t for t in tasks if t.get("module") == "set_fact"]
        total_tasks = len(tasks)
        set_fact_count = len(set_fact_tasks)

        # Calculate percentage
        if total_tasks > 0:
            percentage = (set_fact_count / total_tasks) * 100

            # Threshold: >15% of tasks are set_fact
            if percentage > 15 and set_fact_count > 5:
                suggestions.append(
                    SimplificationSuggestion(
                        pattern="excessive_set_fact",
                        category=self.pattern_category,
                        severity=SeverityLevel.INFO,
                        description=f"{set_fact_count} set_fact tasks ({percentage:.1f}% of all tasks)",
                        example=self._show_task_snippet(set_fact_tasks[:3]),
                        suggestion=Suggestion.excessive_set_fact(),
                        affected_files=self._get_unique_files(set_fact_tasks),
                        impact="Reduces cognitive load and improves performance (fewer task executions)",
                        confidence=self._CONFIDENCE_LEVEL_EXCESSIVE_SET_FACTS,
                    )
                )

        return suggestions
