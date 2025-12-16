"""Detectors for complexity anti-patterns.

Identifies overly complex logic, conditionals, and control flow
that make roles hard to understand and maintain.
"""

from typing import List, Dict, Any
from docsible.analyzers.patterns.base import BasePatternDetector
from docsible.analyzers.patterns.models import (
    SimplificationSuggestion,
    SeverityLevel,
    PatternCategory
)


class ComplexityDetector(BasePatternDetector):
    """Detects complexity anti-patterns."""

    @property
    def pattern_category(self) -> PatternCategory:
        """Return complexity category."""
        return PatternCategory.COMPLEXITY

    def detect(self, role_info: Dict[str, Any]) -> List[SimplificationSuggestion]:
        """Detect all complexity patterns.

        Args:
            role_info: Parsed role information

        Returns:
            List of suggestions for reducing complexity
        """
        suggestions = []

        suggestions.extend(self._detect_complex_conditionals(role_info))
        suggestions.extend(self._detect_deep_include_chains(role_info))
        suggestions.extend(self._detect_excessive_set_fact(role_info))

        return suggestions

    def _detect_complex_conditionals(
        self, role_info: Dict[str, Any]
    ) -> List[SimplificationSuggestion]:
        """Find overly complex 'when' conditions.

        Example anti-pattern:
            when: (ansible_os_family == "Debian" and ansible_distribution_major_version >= "18")
                  or (ansible_os_family == "RedHat" and ansible_distribution_major_version >= "7")
                  or custom_flag is defined and custom_flag == true

        Better:
            Set intermediate facts or split into separate task files
        """
        suggestions = []

        for task_file in self._get_task_files(role_info):
            file_name = task_file.get('file', 'unknown')

            for task in task_file.get('tasks', []):
                when = task.get('when')
                if not when:
                    continue

                # Convert to string for analysis
                when_str = str(when) if not isinstance(when, list) else ' and '.join(map(str, when))

                # Count boolean operators
                or_count = when_str.lower().count(' or ')
                and_count = when_str.lower().count(' and ')
                total_operators = or_count + and_count

                # Detect complex conditionals
                # Threshold: More than 2 ORs or more than 3 ANDs
                is_complex = or_count > 2 or and_count > 3 or total_operators > 5

                if is_complex:
                    suggestions.append(SimplificationSuggestion(
                        pattern="complex_conditional",
                        category=self.pattern_category,
                        severity=SeverityLevel.INFO,
                        description=f"Complex conditional in task '{task.get('name', 'unnamed')}' ({total_operators} operators)",
                        example=f"when: {when_str[:150]}..." if len(when_str) > 150 else f"when: {when_str}",
                        suggestion=(
                            "Simplify complex conditionals:\n\n"
                            "**Option 1: Use intermediate facts**\n"
                            "```yaml\n"
                            "- name: Determine if action needed\n"
                            "  set_fact:\n"
                            "    should_run: \"{{ (condition1) or (condition2) }}\"\n"
                            "\n"
                            "- name: Your task\n"
                            "  ...\n"
                            "  when: should_run | bool\n"
                            "```\n\n"
                            "**Option 2: Split into separate files**\n"
                            "```yaml\n"
                            "# main.yml\n"
                            "- include_tasks: debian_setup.yml\n"
                            "  when: ansible_os_family == 'Debian'\n"
                            "\n"
                            "- include_tasks: redhat_setup.yml\n"
                            "  when: ansible_os_family == 'RedHat'\n"
                            "```\n\n"
                            "**Option 3: Use block conditionals**\n"
                            "```yaml\n"
                            "- block:\n"
                            "    - name: Task 1\n"
                            "    - name: Task 2\n"
                            "  when: complex_condition\n"
                            "```"
                        ),
                        affected_files=[file_name],
                        impact="Improves readability and testability",
                        confidence=0.85
                    ))

        return suggestions

    def _detect_deep_include_chains(
        self, role_info: Dict[str, Any]
    ) -> List[SimplificationSuggestion]:
        """Detect deeply nested include_tasks/import_tasks chains.

        Example anti-pattern:
            main.yml → setup.yml → prereqs.yml → install_deps.yml (4 levels)

        Better:
            Flatten to 2-3 levels maximum
        """
        suggestions = []

        # Build include graph
        include_graph = {}
        for task_file in self._get_task_files(role_info):
            file_name = task_file.get('file', 'unknown')
            includes = []

            for task in task_file.get('tasks', []):
                module = task.get('module', '')
                if module in ['include_tasks', 'import_tasks', 'include_role', 'import_role']:
                    # Try to extract included file
                    included = task.get('file') or task.get('name', '').split()[-1]
                    includes.append(included)

            include_graph[file_name] = includes

        # Calculate max depth using DFS
        def calculate_depth(file_name: str, visited: set) -> int:
            """Calculate maximum include depth from this file."""
            if file_name in visited:
                return 0  # Cycle detected, stop
            if file_name not in include_graph:
                return 1

            visited.add(file_name)
            max_child_depth = 0

            for included in include_graph[file_name]:
                depth = calculate_depth(included, visited.copy())
                max_child_depth = max(max_child_depth, depth)

            return 1 + max_child_depth

        # Check depth starting from main.yml
        if 'main.yml' in include_graph:
            depth = calculate_depth('main.yml', set())

            if depth > 3:
                # Build chain representation
                chain_example = " → ".join(list(include_graph.keys())[:depth])

                suggestions.append(SimplificationSuggestion(
                    pattern="deep_include_chain",
                    category=self.pattern_category,
                    severity=SeverityLevel.WARNING,
                    description=f"Include chain depth is {depth} levels (recommended: ≤3)",
                    example=f"Chain example: {chain_example}",
                    suggestion=(
                        "Reduce include nesting:\n\n"
                        "**Current structure:**\n"
                        "```\n"
                        "main.yml → file1.yml → file2.yml → file3.yml\n"
                        "```\n\n"
                        "**Flattened structure:**\n"
                        "```yaml\n"
                        "# main.yml\n"
                        "- import_tasks: install.yml\n"
                        "- import_tasks: configure.yml\n"
                        "- import_tasks: services.yml\n"
                        "```\n\n"
                        "Keep hierarchy shallow (2-3 levels max) for easier debugging."
                    ),
                    affected_files=list(include_graph.keys()),
                    impact="Easier debugging and flow understanding",
                    confidence=0.9
                ))

        return suggestions

    def _detect_excessive_set_fact(
        self, role_info: Dict[str, Any]
    ) -> List[SimplificationSuggestion]:
        """Detect overuse of set_fact tasks.

        Example anti-pattern:
            20% or more of tasks are just variable assignments

        Better:
            Use vars: at play/task level, or role defaults
        """
        suggestions = []

        tasks = self._flatten_tasks(role_info)
        if not tasks:
            return suggestions

        set_fact_tasks = [t for t in tasks if t.get('module') == 'set_fact']
        total_tasks = len(tasks)
        set_fact_count = len(set_fact_tasks)

        # Calculate percentage
        if total_tasks > 0:
            percentage = (set_fact_count / total_tasks) * 100

            # Threshold: >15% of tasks are set_fact
            if percentage > 15 and set_fact_count > 5:
                suggestions.append(SimplificationSuggestion(
                    pattern="excessive_set_fact",
                    category=self.pattern_category,
                    severity=SeverityLevel.INFO,
                    description=f"{set_fact_count} set_fact tasks ({percentage:.1f}% of all tasks)",
                    example=self._show_task_snippet(set_fact_tasks[:3]),
                    suggestion=(
                        "Reduce set_fact usage:\n\n"
                        "**1. Use role defaults/vars instead:**\n"
                        "```yaml\n"
                        "# defaults/main.yml\n"
                        "computed_value: \"{{ base_value | default('default') }}\"\n"
                        "```\n\n"
                        "**2. Use vars at task level:**\n"
                        "```yaml\n"
                        "- name: Task that needs variable\n"
                        "  debug:\n"
                        "    msg: \"{{ my_var }}\"\n"
                        "  vars:\n"
                        "    my_var: \"{{ complex_expression }}\"\n"
                        "```\n\n"
                        "**3. Use Jinja2 filters directly:**\n"
                        "```yaml\n"
                        "# Instead of:\n"
                        "- set_fact: upper_name=\"{{ name | upper }}\"\n"
                        "- debug: msg=\"{{ upper_name }}\"\n"
                        "\n"
                        "# Just use:\n"
                        "- debug: msg=\"{{ name | upper }}\"\n"
                        "```\n\n"
                        "Reserve set_fact for truly dynamic values that change during playbook execution."
                    ),
                    affected_files=self._get_unique_files(set_fact_tasks),
                    impact="Reduces cognitive load and improves performance (fewer task executions)",
                    confidence=0.75
                ))

        return suggestions
