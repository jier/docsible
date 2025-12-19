"""
Analyzers for role complexity, integration detection, and documentation quality.

This package provides tools to analyze Ansible roles and determine:
- Complexity metrics (task count, conditionals, composition)
- External system integrations
- Appropriate visualization strategies
"""

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    ComplexityReport,
    IntegrationPoint,
    analyze_role_complexity,
)

__all__ = [
    "ComplexityCategory",
    "ComplexityMetrics",
    "ComplexityReport",
    "IntegrationPoint",
    "analyze_role_complexity",
]
