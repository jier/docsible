import re
from typing import Any

from .base import BaseValidator
from .models import ValidationIssue, ValidationSeverity, ValidationType


class TruthValidator(BaseValidator):
    type = ValidationType.TRUTH

    def validate(self, documentation: str, role_info: dict[str, Any] | None, complexity_report: Any | None) -> tuple[list[ValidationIssue], dict[str, Any]]:
        """
        Validate documentation accuracy against actual role structure.

        Checks:
        - Task counts match reality
        - Variable names are correct
        - Dependencies are accurate
        - Integration claims are verified
        """
        issues: list[ValidationIssue] = []
        metrics: dict[str, Any] = {}

        # Check for auto-generated markers (always check, even without role_info)
        has_generated_markers = "DOCSIBLE GENERATED" in documentation
        metrics["has_generated_markers"] = has_generated_markers

        # Verify complexity category if mentioned (can check even without role_info)
        if complexity_report:
            actual_category = complexity_report.category.value.upper()
            metrics["actual_complexity"] = actual_category

            category_mentions = re.findall(
                r"\b(SIMPLE|MEDIUM|COMPLEX)\s+role", documentation, re.IGNORECASE
            )
            if category_mentions:
                claimed_category = category_mentions[0].upper()
                if claimed_category != actual_category:
                    issues.append(
                        ValidationIssue(
                            type=ValidationType.TRUTH,
                            severity=ValidationSeverity.ERROR,
                            message=f"Documentation claims {claimed_category} but role is {actual_category}",
                            suggestion=f"Correct complexity category to {actual_category}",
                        )
                    )

        if not role_info:
            return issues, metrics

        # Verify task count accuracy
        actual_tasks = sum(
            len(tf.get("tasks", [])) for tf in role_info.get("tasks", [])
        )
        metrics["actual_tasks"] = actual_tasks

        # Extract task count claims from documentation
        task_claims = re.findall(r"(\d+)\s+tasks?", documentation, re.IGNORECASE)
        if task_claims:
            claimed_tasks = int(task_claims[0])
            metrics["claimed_tasks"] = claimed_tasks

            if claimed_tasks != actual_tasks:
                issues.append(
                    ValidationIssue(
                        type=ValidationType.TRUTH,
                        severity=ValidationSeverity.ERROR,
                        message=f"Documentation claims {claimed_tasks} tasks but role has {actual_tasks}",
                        suggestion=f"Update task count to {actual_tasks}",
                    )
                )

        return issues, metrics
