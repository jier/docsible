"""Detectors for security anti-patterns.

Identifies potential security issues like exposed secrets,
missing no_log directives, and insecure defaults.
"""

from typing import Any

from docsible.analyzers.patterns.base import BasePatternDetector
from docsible.analyzers.patterns.detectors.suggestions.security_suggestion import Suggestion
from docsible.analyzers.patterns.models import (
    PatternCategory,
    SeverityLevel,
    SimplificationSuggestion,
)


class SecurityDetector(BasePatternDetector):
    """Detects security anti-patterns."""
    #FIXME Should secret indicators not be pluggable?
    # Variable names that often contain secrets
    SECRET_INDICATORS = [
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "private_key",
        "priv_key",
        "credential",
        "auth",
        "access_key",
        "secret_key",
    ]

    @property
    def pattern_category(self) -> PatternCategory:
        """Return security category."""
        return PatternCategory.SECURITY

    def detect(self, role_info: dict[str, Any]) -> list[SimplificationSuggestion]:
        """Detect all security patterns.

        Args:
            role_info: Parsed role information

        Returns:
            List of suggestions for improving security
        """
        suggestions: list[SimplificationSuggestion] = []

        suggestions.extend(self._detect_exposed_secrets(role_info))
        suggestions.extend(self._detect_missing_no_log(role_info))
        suggestions.extend(self._detect_insecure_permissions(role_info))
        suggestions.extend(self._detect_shell_injection_risks(role_info))

        return suggestions

    def _detect_exposed_secrets(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Find potential secrets in plain text.

        Looks for variables with secret-like names that aren't
        using ansible-vault or proper secret management.
        """
        suggestions: list[SimplificationSuggestion] = []

        # Check defaults and vars
        for var_type in ["defaults", "vars"]:
            variables = role_info.get(var_type, {})

            # Handle both dict and list formats
            if isinstance(variables, list):
                # Convert list of dicts to single dict
                temp_vars = {}
                for item in variables:
                    if isinstance(item, dict):
                        temp_vars.update(item)
                variables = temp_vars

            exposed_secrets = []

            for var_name, var_value in variables.items():
                # Check if variable name suggests it's a secret
                if any(
                    indicator in var_name.lower()
                    for indicator in self.SECRET_INDICATORS
                ):
                    # Check if value looks like plain text (not encrypted or templated)
                    value_str = str(var_value)
                    is_plain = not value_str.startswith(
                        "{{"
                    ) and not value_str.startswith("!vault")

                    if is_plain and len(value_str) > 0:
                        exposed_secrets.append((var_name, value_str))

            if exposed_secrets:
                example_vars = "\n".join(
                    [
                        f"{name}: {value[:20]}..."
                        if len(value) > 20
                        else f"{name}: {value}"
                        for name, value in exposed_secrets[:3]
                    ]
                )

                suggestions.append(
                    SimplificationSuggestion(
                        pattern="exposed_secrets",
                        category=self.pattern_category,
                        severity=SeverityLevel.CRITICAL,
                        description=f"Found {len(exposed_secrets)} potential secrets in {var_type}/ without encryption",
                        example=f"```yaml\n{example_vars}\n```",
                        suggestion=Suggestion.exposed_secrets(var_type=var_type),
                        affected_files=[f"{var_type}/main.yml"],
                        impact="Prevents credential exposure and unauthorized access",
                        confidence=0.8,
                    )
                )

        return suggestions

    def _detect_missing_no_log(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Find tasks handling secrets without no_log directive.

        Tasks that register variables with secret-like names or
        use modules like set_fact with secrets should have no_log: true.
        """
        suggestions: list[SimplificationSuggestion] = []

        risky_tasks = []

        for task in self._flatten_tasks(role_info):
            task_name = task.get("name", "").lower()
            module = task.get("module", "")
            has_no_log = task.get("no_log", False)

            # Check if task involves secrets
            involves_secrets = any(
                indicator in task_name for indicator in self.SECRET_INDICATORS
            )

            # Special check for set_fact with secret variables
            if module == "set_fact" and not has_no_log:
                # Check if any of the set variables look like secrets
                for key in task.keys():
                    if any(
                        indicator in key.lower() for indicator in self.SECRET_INDICATORS
                    ):
                        involves_secrets = True
                        break

            if involves_secrets and not has_no_log:
                risky_tasks.append(task)

        if risky_tasks:
            suggestions.append(
                SimplificationSuggestion(
                    pattern="missing_no_log",
                    category=self.pattern_category,
                    severity=SeverityLevel.WARNING,
                    description=f"Found {len(risky_tasks)} tasks handling secrets without 'no_log: true'",
                    example=self._show_task_snippet(risky_tasks[:2]),
                    suggestion=Suggestion.missing_no_log(),
                    affected_files=self._get_unique_files(risky_tasks),
                    impact="Prevents secrets from appearing in Ansible logs",
                    confidence=0.85,
                )
            )

        return suggestions

    def _detect_insecure_permissions(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Find file/directory operations with overly permissive modes.

        Example: mode: '0777' on sensitive files
        """
        suggestions: list[SimplificationSuggestion] = []

        file_tasks = self._get_tasks_by_module(role_info, "file")
        copy_tasks = self._get_tasks_by_module(role_info, "copy")
        template_tasks = self._get_tasks_by_module(role_info, "template")

        all_file_tasks = file_tasks + copy_tasks + template_tasks
        insecure_tasks = []

        for task in all_file_tasks:
            mode = task.get("mode", "")
            mode_str = str(mode)

            # Check for world-writable (777, 666) or group-writable on sensitive files
            is_world_writable = mode_str in ["0777", "777", "0666", "666"]

            # Check if task involves sensitive files
            task_name = task.get("name", "").lower()
            path = task.get("path", task.get("dest", "")).lower()

            is_sensitive = any(
                word in task_name or word in path
                for word in [
                    "key",
                    "cert",
                    "password",
                    "secret",
                    "config",
                    "credential",
                ]
            )

            if is_world_writable or (is_sensitive and not mode):
                insecure_tasks.append((task, mode_str))

        if insecure_tasks:
            example_tasks = [task for task, _ in insecure_tasks[:2]]

            suggestions.append(
                SimplificationSuggestion(
                    pattern="insecure_file_permissions",
                    category=self.pattern_category,
                    severity=SeverityLevel.WARNING,
                    description=f"Found {len(insecure_tasks)} file operations with insecure permissions",
                    example=self._show_task_snippet(example_tasks),
                    suggestion=Suggestion.insecure_permission(),
                    affected_files=self._get_unique_files(example_tasks),
                    impact="Prevents unauthorized access to sensitive files",
                    confidence=0.9,
                )
            )

        return suggestions

    def _detect_shell_injection_risks(
        self, role_info: dict[str, Any]
    ) -> list[SimplificationSuggestion]:
        """Find shell/command tasks with user-controlled input.

        Example anti-pattern:
            shell: "rm -rf {{ user_input }}"  ← Injection risk!
        """
        suggestions: list[SimplificationSuggestion] = []

        shell_tasks = self._get_tasks_by_module(role_info, "shell")
        command_tasks = self._get_tasks_by_module(role_info, "command")

        all_shell_tasks = shell_tasks + command_tasks
        risky_tasks = []

        for task in all_shell_tasks:
            # Get the command (could be in different places)
            cmd = task.get("cmd", task.get("command", task.get("shell", "")))
            cmd_str = str(cmd)

            # Check if command contains variables (potential injection point)
            has_variables = "{{" in cmd_str

            # Check for dangerous patterns
            has_rm = " rm " in cmd_str or cmd_str.startswith("rm ")
            has_eval = "eval" in cmd_str
            has_pipe_to_shell = "| sh" in cmd_str or "| bash" in cmd_str

            is_risky = has_variables and (has_rm or has_eval or has_pipe_to_shell)

            if is_risky:
                risky_tasks.append(task)

        if risky_tasks:
            suggestions.append(
                SimplificationSuggestion(
                    pattern="shell_injection_risk",
                    category=self.pattern_category,
                    severity=SeverityLevel.CRITICAL,
                    description=f"Found {len(risky_tasks)} shell/command tasks with potential injection risks",
                    example=self._show_task_snippet(risky_tasks[:2]),
                    suggestion=Suggestion.shell_injection_risks(),
                    affected_files=self._get_unique_files(risky_tasks),
                    impact="Prevents arbitrary command execution vulnerabilities",
                    confidence=0.75,
                )
            )

        return suggestions
