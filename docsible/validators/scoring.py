from typing import Any

from .models import ValidationIssue, ValidationSeverity


def calculate_score(
         issues: list[ValidationIssue], metrics: dict[str, Any]
    ) -> float:
        """
        Calculate overall quality score (0-100).

        Scoring:
        - Start at 100
        - ERROR: -15 points each
        - WARNING: -5 points each
        - INFO: -2 points each
        - Floor at 0
        """
        score = 100.0

        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                score -= 15.0
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 5.0
            elif issue.severity == ValidationSeverity.INFO:
                score -= 2.0

        return max(0.0, score)