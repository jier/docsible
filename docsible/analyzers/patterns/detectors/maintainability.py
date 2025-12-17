"""Detectors for maintainability anti-patterns.

Identifies issues that make roles hard to maintain, test,
and understand over time.
"""

from typing import Any

from docsible.analyzers.patterns.base import BasePatternDetector
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
                    suggestion=(
                        "Make tasks idempotent:\n\n"
                        "**Option 1: Use creates/removes**\n"
                        "```yaml\n"
                        "- name: Download file\n"
                        "  command: wget https://example.com/file.tar.gz\n"
                        "  args:\n"
                        "    creates: /tmp/file.tar.gz  # Skip if file exists\n"
                        "\n"
                        "- name: Remove old config\n"
                        "  command: rm /etc/old.conf\n"
                        "  args:\n"
                        "    removes: /etc/old.conf  # Skip if file doesn't exist\n"
                        "```\n\n"
                        "**Option 2: Use changed_when**\n"
                        "```yaml\n"
                        "- name: Check service status\n"
                        "  command: systemctl is-active myapp\n"
                        "  register: result\n"
                        "  changed_when: false  # Never report as changed\n"
                        "  failed_when: false   # Don't fail if not active\n"
                        "```\n\n"
                        "**Option 3: Use check mode**\n"
                        "```yaml\n"
                        "- name: Configure app\n"
                        "  shell: /usr/local/bin/configure.sh\n"
                        "  changed_when: result.rc == 0\n"
                        "  check_mode: no  # Always run in check mode\n"
                        "  register: result\n"
                        "```\n\n"
                        "**Best: Use native modules instead**\n"
                        "```yaml\n"
                        "# Instead of: shell: wget ...\n"
                        "- name: Download file\n"
                        "  get_url:\n"
                        "    url: https://example.com/file.tar.gz\n"
                        "    dest: /tmp/file.tar.gz\n"
                        "  # Automatically idempotent!\n"
                        "```"
                    ),
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
                        suggestion=(
                            "Split into logical files:\n\n"
                            "```yaml\n"
                            "# tasks/main.yml - Orchestration only\n"
                            "---\n"
                            "- import_tasks: validate.yml\n"
                            "- import_tasks: install.yml\n"
                            "- import_tasks: configure.yml\n"
                            "- import_tasks: services.yml\n"
                            "```\n\n"
                            "```yaml\n"
                            "# tasks/install.yml - Package installation\n"
                            "---\n"
                            "- name: Install dependencies\n"
                            "  apt:\n"
                            '    name: "{{ item }}"\n'
                            '  loop: "{{ app_dependencies }}"\n'
                            "```\n\n"
                            "```yaml\n"
                            "# tasks/configure.yml - Configuration\n"
                            "---\n"
                            "- name: Copy configuration\n"
                            "  template:\n"
                            "    src: app.conf.j2\n"
                            "    dest: /etc/app.conf\n"
                            "```\n\n"
                            "**Benefits:**\n"
                            "- Easier to find specific functionality\n"
                            "- Can reuse files with include_tasks conditionally\n"
                            "- Better for testing individual components\n"
                            "- Clearer separation of concerns"
                        ),
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
                    example=f"```\n{example}\n```",
                    suggestion=(
                        "Replace magic values with variables:\n\n"
                        "**Instead of hardcoding:**\n"
                        "```yaml\n"
                        "- name: Create directory\n"
                        "  file:\n"
                        "    path: /opt/myapp  # ← Hardcoded\n"
                        "    state: directory\n"
                        "\n"
                        "- name: Copy config\n"
                        "  copy:\n"
                        "    dest: /opt/myapp/config.yml  # ← Repeated\n"
                        "```\n\n"
                        "**Use variables:**\n"
                        "```yaml\n"
                        "# defaults/main.yml\n"
                        "app_install_dir: /opt/myapp\n"
                        'app_config_file: "{{ app_install_dir }}/config.yml"\n'
                        "```\n\n"
                        "```yaml\n"
                        "# tasks/main.yml\n"
                        "- name: Create directory\n"
                        "  file:\n"
                        '    path: "{{ app_install_dir }}"\n'
                        "    state: directory\n"
                        "\n"
                        "- name: Copy config\n"
                        "  copy:\n"
                        '    dest: "{{ app_config_file }}"\n'
                        "```\n\n"
                        "**Benefits:**\n"
                        "- Single source of truth\n"
                        "- Easy to change paths\n"
                        "- Better for multi-environment deployments"
                    ),
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
                    suggestion=(
                        "Support check mode (ansible-playbook --check):\n\n"
                        "**Problem:**\n"
                        "```yaml\n"
                        "- name: Get app version\n"
                        "  command: /opt/app --version\n"
                        "  register: app_version  # ← Fails in check mode\n"
                        "\n"
                        "- name: Upgrade if old\n"
                        "  apt: name=myapp\n"
                        "  when: app_version.stdout is version('2.0', '<')\n"
                        "  # ↑ Error: app_version undefined in check mode\n"
                        "```\n\n"
                        "**Solution:**\n"
                        "```yaml\n"
                        "- name: Get app version\n"
                        "  command: /opt/app --version\n"
                        "  register: app_version\n"
                        "  check_mode: no  # ← Always run, even in check mode\n"
                        "  changed_when: false\n"
                        "\n"
                        "- name: Upgrade if old\n"
                        "  apt: name=myapp\n"
                        "  when: app_version.stdout is version('2.0', '<')\n"
                        "  # Works in check mode now!\n"
                        "```\n\n"
                        "Check mode lets you test playbooks safely without making changes."
                    ),
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
                    suggestion=(
                        "Handle pipeline failures explicitly:\n\n"
                        "**Problem:**\n"
                        "```yaml\n"
                        "- name: Check service running\n"
                        "  shell: systemctl status app | grep 'active'\n"
                        "  # ↑ If systemctl fails, grep might still succeed\n"
                        "  #   Or if grep fails (no match), task fails unexpectedly\n"
                        "```\n\n"
                        "**Solution:**\n"
                        "```yaml\n"
                        "- name: Check service running\n"
                        "  shell: |\n"
                        "    set -o pipefail  # ← Fail if any command in pipeline fails\n"
                        "    systemctl status app | grep 'active'\n"
                        "  args:\n"
                        "    executable: /bin/bash\n"
                        "  register: result\n"
                        "  failed_when: result.rc not in [0, 1]  # ← Explicit handling\n"
                        "  changed_when: false\n"
                        "```\n\n"
                        "**Better - Use native modules:**\n"
                        "```yaml\n"
                        "- name: Check service running\n"
                        "  service_facts:\n"
                        "\n"
                        "- name: Verify app is active\n"
                        "  assert:\n"
                        "    that:\n"
                        "      - ansible_facts.services['app.service'].state == 'running'\n"
                        "```"
                    ),
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
                    suggestion=(
                        "Avoid variable shadowing:\n\n"
                        "**Variable Precedence in Ansible** (lowest to highest):\n"
                        "```\n"
                        "1. defaults/main.yml         ← Lowest (easily overridden)\n"
                        "2. group_vars/\n"
                        "3. host_vars/\n"
                        "4. playbook vars:\n"
                        "5. vars/main.yml             ← High precedence\n"
                        "6. extra_vars (-e)           ← Highest\n"
                        "```\n\n"
                        "**Best practices:**\n\n"
                        "**Use defaults/ for:**\n"
                        "```yaml\n"
                        "# defaults/main.yml\n"
                        "app_port: 8080          # Can be overridden by users\n"
                        "app_user: appuser       # Sensible defaults\n"
                        "```\n\n"
                        "**Use vars/ for:**\n"
                        "```yaml\n"
                        "# vars/main.yml\n"
                        "app_config_dir: /etc/app      # Internal constants\n"
                        "app_required_packages:        # Computed values\n"
                        '  - "{{ app_name }}-core"\n'
                        "```\n\n"
                        "**Don't define the same variable in both!**\n"
                        "Choose one location based on whether users should override it."
                    ),
                    affected_files=["defaults/main.yml", "vars/main.yml"],
                    impact="Eliminates confusion about which value will be used",
                    confidence=0.95,
                )
            )

        return suggestions
