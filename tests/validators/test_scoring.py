"""Tests for scoring calculations."""

from docsible.validators.models import (
    ValidationIssue,
    ValidationSeverity,
    ValidationType,
)
from docsible.validators.scoring import calculate_score


class TestScoreCalculation:
    """Test quality score calculation."""

    def test_score_calculation_with_errors(self):
        """Test score calculation with ERROR severity issues."""
        issues_severe = [
            ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.ERROR,
                message="Error 1",
            ),
            ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.ERROR,
                message="Error 2",
            ),
        ]

        score_severe = calculate_score(issues_severe)
        # 100 - (2 * 15) = 70
        assert score_severe == 70.0

    def test_score_calculation_with_mixed_severities(self):
        """Test score calculation with mixed severity issues."""
        issues_mixed = [
            ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.ERROR,
                message="Error",
            ),
            ValidationIssue(
                type=ValidationType.MAINTENANCE,
                severity=ValidationSeverity.WARNING,
                message="Warning",
            ),
            ValidationIssue(
                type=ValidationType.VALUE,
                severity=ValidationSeverity.INFO,
                message="Info",
            ),
        ]

        score_mixed = calculate_score(issues_mixed)
        # 100 - 15 - 5 - 2 = 78
        assert score_mixed == 78.0

    def test_score_floor_at_zero(self):
        """Test that score cannot go below 0."""
        # Create many errors to exceed 100 points
        issues = [
            ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.ERROR,
                message=f"Error {i}",
            )
            for i in range(10)
        ]

        score = calculate_score(issues)
        # 100 - (10 * 15) = -50, but floored at 0
        assert score == 0.0

    def test_perfect_score(self):
        """Test that no issues results in perfect score."""
        issues: list[ValidationIssue] = []
        score = calculate_score(issues)
        assert score == 100.0
