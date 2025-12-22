from typing import Any

from .models import ValidationIssue, ValidationSeverity


def calculate_score(
         issues: list[ValidationIssue]
    ) -> float:
        """
        Calculate overall quality score (0-100).

        Note: Currently only uses issues for scoring. Metrics could be
        incorporated in the future for more nuanced scoring (e.g., rewarding
        comprehensive documentation, penalizing brevity, etc.).

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

def _calculate_metric_adjustments(metrics: dict[str, Any]) :
    """
    Calculate score adjustments based on quality metrics.
    
    Bonuses:
    - Has diagrams for complex roles: +5 points
    - High section coverage: +3 points
    - Good example coverage: +2 points
    
    Penalties:
    - Low word count: -5 points
    - Missing key sections: -3 points
    
    Args:
        metrics: Quality metrics from all validators
        
    Returns:
        Adjustment value (can be positive or negative flow)
    """
    raise NotImplementedError("Should be done in the near future")