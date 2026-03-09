"""Complexity classification logic."""

from ..models import ComplexityCategory, ComplexityMetrics


def classify_complexity(metrics: ComplexityMetrics) -> ComplexityCategory:
    """Classify role complexity using multiple factors.

    Primary classification is based on total task count. Additional factors
    can promote a role to a higher category:
    - composition_score > 8: role orchestrates many other roles/tasks
    - conditional_percentage > 60: more than 60% of tasks are conditional
    - external_integrations > 3: touches many external systems

    Enterprise classification requires high task count AND high complexity
    in at least one secondary dimension.

    Thresholds:
    - Simple:     1-10 tasks, no promoting factors
    - Medium:     11-25 tasks, or 1-10 tasks with high composition/conditionals
    - Complex:    26-50 tasks, or lower count promoted by secondary factors
    - Enterprise: 50+ tasks with high integration/composition complexity
    """
    total = metrics.total_tasks
    composition = metrics.composition_score
    conditional_pct = metrics.conditional_percentage
    integrations = metrics.external_integrations

    # Enterprise: large role with significant orchestration or integration load
    if total > 50 and (integrations > 3 or composition > 10):
        return ComplexityCategory.ENTERPRISE

    # Complex: large task count, OR medium count boosted by secondary factors
    if total > 25:
        return ComplexityCategory.COMPLEX
    if total > 10 and (composition > 8 or conditional_pct > 60 or integrations > 3):
        return ComplexityCategory.COMPLEX

    # Medium: moderate task count, OR small count with notable orchestration
    if total > 10:
        return ComplexityCategory.MEDIUM
    if total > 0 and (composition > 4 or conditional_pct > 40):
        return ComplexityCategory.MEDIUM

    # Simple: small, straightforward role
    return ComplexityCategory.SIMPLE
