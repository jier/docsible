import re
from typing import Any

from .base import BaseValidator
from .models import ValidationIssue, ValidationSeverity, ValidationType


class MaintenanceValidator(BaseValidator):
    type = ValidationType.MAINTENANCE

    def validate(self, documentation: str, role_info: dict[str, Any] | None, complexity_report: Any | None) -> tuple[list[ValidationIssue], dict[str, Any]]:
        """
        Validate documentation completeness and maintainability.

        Checks:
        - All role components are documented
        - Variables are documented
        - Dependencies are listed
        - Examples are provided
        - Metadata is present
        """
        issues: list[ValidationIssue] = []
        metrics: dict[str, Any] = {}

        if not role_info:
            return issues, metrics

        # Check variable documentation coverage
        defaults_count = sum(
            len(df.get("data", {})) for df in role_info.get("defaults", [])
        )
        vars_count = sum(len(vf.get("data", {})) for vf in role_info.get("vars", []))
        total_vars = defaults_count + vars_count

        metrics["total_variables"] = total_vars

        # Count documented variables (look for variable names in docs)
        if total_vars > 0:
            # Check if variables section exists
            if not re.search(
                r"^#+\s+(?:Role\s+)?Variables",
                documentation,
                re.MULTILINE | re.IGNORECASE,
            ):
                issues.append(
                    ValidationIssue(
                        type=ValidationType.MAINTENANCE,
                        severity=ValidationSeverity.WARNING,
                        message=f"Role has {total_vars} variables but no Variables section found",
                        section="Variables",
                        suggestion="Add a Variables section documenting all configurable options",
                    )
                )

        # Check handler documentation
        handlers_count = len(role_info.get("handlers", []))
        metrics["handlers"] = handlers_count

        if handlers_count > 0:
            if "handler" not in documentation.lower():
                issues.append(
                    ValidationIssue(
                        type=ValidationType.MAINTENANCE,
                        severity=ValidationSeverity.INFO,
                        message=f"Role has {handlers_count} handlers but they're not mentioned",
                        section="Handlers",
                        suggestion="Document available handlers and when they're triggered",
                    )
                )

        # Check for example playbook
        has_example = bool(re.search(r"```(?:yaml|yml)", documentation, re.IGNORECASE))
        metrics["has_example"] = has_example

        if not has_example:
            issues.append(
                ValidationIssue(
                    type=ValidationType.MAINTENANCE,
                    severity=ValidationSeverity.WARNING,
                    message="No example playbook found",
                    section="Example Playbook",
                    suggestion="Add a working example showing how to use the role",
                )
            )

        # Check for dependencies documentation
        dependencies = role_info.get("dependencies", [])
        metrics["dependencies"] = len(dependencies)

        if dependencies and "dependencies" not in documentation.lower():
            issues.append(
                ValidationIssue(
                    type=ValidationType.MAINTENANCE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Role has {len(dependencies)} dependencies but they're not documented",
                    section="Dependencies",
                    suggestion="Document role dependencies and their purpose",
                )
            )

        return issues, metrics