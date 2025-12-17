"""Complexity analyzer for Ansible roles.

Analyzes role complexity by counting tasks, conditionals, role composition,
and external integrations to determine appropriate documentation strategy.

This module has been modularized for better maintainability:
- models.py: Data models (Pydantic)
- integrations/: External integration detection
- analyzers/: Complexity analysis logic
- hotspots.py: Conditional complexity detection
- inflections.py: Branching point detection
- recommendations.py: Recommendation generation

Backward Compatibility:
All previous public APIs are maintained via re-exports below.
"""

# Re-export all public APIs for backward compatibility
from .analyzers import (
    analyze_file_complexity,
    analyze_role_complexity,
    classify_complexity,
)
from .hotspots import detect_conditional_hotspots
from .inflections import detect_inflection_points
from .integrations import IntegrationDetector, detect_integrations
from .models import (
    ComplexityCategory,
    ComplexityMetrics,
    ComplexityReport,
    ConditionalHotspot,
    FileComplexityDetail,
    InflectionPoint,
    IntegrationPoint,
    IntegrationType,
)
from .recommendations import generate_recommendations

__all__ = [
    # Data models
    "ComplexityCategory",
    "IntegrationType",
    "IntegrationPoint",
    "ComplexityMetrics",
    "FileComplexityDetail",
    "ComplexityReport",
    "ConditionalHotspot",
    "InflectionPoint",
    # Integration detection
    "IntegrationDetector",
    "detect_integrations",
    # Analysis functions
    "analyze_file_complexity",
    "analyze_role_complexity",
    "classify_complexity",
    "detect_conditional_hotspots",
    "detect_inflection_points",
    "generate_recommendations",
]
