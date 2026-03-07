from pathlib import Path

from docsible.models.recommendation import Recommendation

from .enhancement import EnhancementRecommendationGenerator
from .quality import QualityRecommendationGenerator
from .security import SecurityRecommendationGenerator


def generate_all_recommendations(role_path: Path) -> list[Recommendation]:
    """Generate all recommendations for a role.

    Args:
        role_path: Path to Ansible role

    Returns:
        List of recommendations sorted by severity (critical first)
    """
    all_recommendations = []

    # Security (CRITICAL)
    security_gen = SecurityRecommendationGenerator()
    all_recommendations.extend(security_gen.analyze_role(role_path))

    # Quality (WARNING)
    quality_gen = QualityRecommendationGenerator()
    all_recommendations.extend(quality_gen.analyze_role(role_path))

    # Enhancements (INFO)
    enhancement_gen = EnhancementRecommendationGenerator()
    all_recommendations.extend(enhancement_gen.analyze_role(role_path))

    # Sort by severity (critical first)
    all_recommendations.sort(
        key=lambda r: r.severity.priority,
        reverse=True
    )

    return all_recommendations