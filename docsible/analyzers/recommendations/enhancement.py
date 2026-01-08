from pathlib import Path

from docsible.models.recommendation import Recommendation
from docsible.models.severity import Severity


class EnhancementRecommendationGenerator:
    """Generate enhancement/best-practice suggestions."""

    def analyze_role(self, role_path: Path) -> list[Recommendation]:
        """Analyze role for potential enhancements."""
        recommendations = []

        # Check for examples directory
        if not (role_path / "examples").exists():
            recommendations.append(Recommendation(
                category="best_practices",
                message="Consider adding examples/ directory",
                rationale="Example playbooks help users understand how to use the role",
                severity=Severity.INFO,
                file_path=None,  # No specific file - this is about missing directory
                line_number=None,  # No specific line
                remediation="Create examples/ with sample playbook.yml",
                confidence=0.6,
                auto_fixable=False,
            ))

        # Check for molecule tests
        if not (role_path / "molecule").exists():
            recommendations.append(Recommendation(
                category="testing",
                message="Consider adding Molecule tests",
                rationale="Automated testing prevents regressions",
                severity=Severity.INFO,
                file_path=None,  # No specific file - this is about missing directory
                line_number=None,  # No specific line
                remediation="Run: molecule init scenario",
                confidence=0.7,
                auto_fixable=False,
            ))

        return recommendations