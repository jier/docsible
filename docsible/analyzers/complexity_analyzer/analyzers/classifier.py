"""Complexity classification logic."""

from ..models import ComplexityCategory, ComplexityMetrics


def classify_complexity(metrics: ComplexityMetrics) -> ComplexityCategory:
    """Classify role complexity based on task count.

    Thresholds:
    - Simple: 1-10 tasks
    - Medium: 11-25 tasks
    - Complex: 25+ tasks

    Args:
        metrics: Complexity metrics

    Returns:
        Complexity category

    Example:
        >>> metrics = ComplexityMetrics(total_tasks=30, ...)
        >>> category = classify_complexity(metrics)
        >>> print(category)
        ComplexityCategory.COMPLEX
    """
    if metrics.total_tasks <= 10:
        return ComplexityCategory.SIMPLE
    elif metrics.total_tasks <= 25:
        return ComplexityCategory.MEDIUM
    else:
        return ComplexityCategory.COMPLEX
