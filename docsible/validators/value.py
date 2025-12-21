import re
from typing import Any

from .base import BaseValidator
from .models import ValidationIssue, ValidationSeverity, ValidationType


class ValueValidator(BaseValidator):
    type = ValidationType.VALUE

    def validate(self, documentation: str, role_info: dict[str, Any] | None, complexity_report: Any | None) -> tuple[list[ValidationIssue], dict[str, Any]]:
        """
        Validate documentation usefulness and actionable content.

        Checks:
        - Provides diagrams for complex roles
        - Includes security considerations for integrations
        - Offers troubleshooting guidance
        - Contains performance tips
        - Has clear examples
        """
        issues: list[ValidationIssue] = []
        metrics: dict[str, Any] = {}

        # Check for diagrams (especially for complex roles)
        has_diagrams = "```mermaid" in documentation
        metrics["has_diagrams"] = has_diagrams

        if complexity_report and complexity_report.category.value in [
            "medium",
            "complex",
        ]:
            if not has_diagrams:
                issues.append(
                    ValidationIssue(
                        type=ValidationType.VALUE,
                        severity=ValidationSeverity.WARNING,
                        message=f"{complexity_report.category.value.upper()} role lacks visual diagrams",
                        suggestion="Add architecture or workflow diagrams for better understanding",
                    )
                )

        # Check for security considerations (especially with integrations)
        has_security = bool(
            re.search(
                r"security|credentials?|authentication", documentation, re.IGNORECASE
            )
        )
        metrics["has_security_guidance"] = has_security

        if complexity_report and complexity_report.integration_points:
            if not has_security:
                issues.append(
                    ValidationIssue(
                        type=ValidationType.VALUE,
                        severity=ValidationSeverity.WARNING,
                        message="Role has external integrations but no security guidance",
                        section="Security",
                        suggestion="Add security considerations for credential management",
                    )
                )

        # Check for actionable examples
        playbook_examples = len(re.findall(r"- hosts:", documentation))
        metrics["playbook_examples"] = playbook_examples

        if playbook_examples == 0:
            issues.append(
                ValidationIssue(
                    type=ValidationType.VALUE,
                    severity=ValidationSeverity.INFO,
                    message="No runnable playbook examples found",
                    suggestion="Add complete playbook examples users can copy",
                )
            )

        # Check for recommendations (from complexity analysis)
        has_recommendations = "recommendation" in documentation.lower()
        metrics["has_recommendations"] = has_recommendations

        # Check content depth (not just structure)
        word_count = len(re.findall(r"\w+", documentation))
        metrics["word_count"] = word_count

        if word_count < 200:
            issues.append(
                ValidationIssue(
                    type=ValidationType.VALUE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Documentation is quite brief ({word_count} words)",
                    suggestion="Consider adding more context and examples",
                )
            )

        return issues, metrics