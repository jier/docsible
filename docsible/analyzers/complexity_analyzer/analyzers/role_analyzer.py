"""Top-level role complexity analysis."""

import logging
from typing import Any

from ..models import ComplexityMetrics, ComplexityReport, IntegrationPoint
from .classifier import classify_complexity
from .file_analyzer import analyze_file_complexity

logger = logging.getLogger(__name__)

# Import pattern analysis (optional dependency)
try:
    from docsible.analyzers.patterns import (
        PatternAnalysisReport,
        analyze_role_patterns,
    )

    PATTERN_ANALYSIS_AVAILABLE = True
except ImportError:
    logger.debug("Pattern analysis not available")
    PATTERN_ANALYSIS_AVAILABLE = False
    PatternAnalysisReport = None  # type: ignore


def analyze_role_complexity(
    role_info: dict[str, Any],
    include_patterns: bool = False,
    min_confidence: float = 0.7,
) -> ComplexityReport:
    """Analyze role complexity and generate comprehensive report.

    Args:
        role_info: Role information dictionary from build_role_info()
        include_patterns: Whether to include pattern analysis (requires --simplification-report flag)
        min_confidence: Minimum confidence threshold for pattern detection (0.0-1.0)

    Returns:
        ComplexityReport with metrics, category, recommendations, and optional pattern analysis

    Example:
        >>> report = analyze_role_complexity(role_info)
        >>> print(f"Category: {report.category}")
        >>> print(f"Total tasks: {report.metrics.total_tasks}")

        >>> # With pattern analysis
        >>> report = analyze_role_complexity(role_info, include_patterns=True)
        >>> if report.pattern_analysis:
        ...     print(f"Health Score: {report.pattern_analysis.overall_health_score}")
    """
    # Import here to avoid circular dependency
    from ..integrations import detect_integrations
    from ..hotspots import detect_conditional_hotspots
    from ..inflections import detect_inflection_points
    from ..recommendations import generate_recommendations

    # Count tasks
    tasks_data = role_info.get("tasks", [])
    total_tasks = sum(len(tf.get("tasks", [])) for tf in tasks_data)
    task_files = len(tasks_data)

    # Count handlers
    handlers = len(role_info.get("handlers", []))

    # Count conditional tasks
    conditional_tasks = sum(
        1 for tf in tasks_data for task in tf.get("tasks", []) if task.get("when")
    )

    # Count tasks with error handling (rescue or always blocks)
    error_handlers = sum(
        1
        for tf in tasks_data
        for task in tf.get("tasks", [])
        if task.get("rescue") or task.get("always")
    )

    # Count role dependencies (from meta/main.yml)
    role_dependencies = len(role_info.get("meta", {}).get("dependencies", []))

    # Count role includes (include_role, import_role)
    role_includes = sum(
        1
        for tf in tasks_data
        for task in tf.get("tasks", [])
        if task.get("module", "")
        in [
            "include_role",
            "import_role",
            "ansible.builtin.include_role",
            "ansible.builtin.import_role",
        ]
    )

    # Count task includes (include_tasks, import_tasks)
    task_includes = sum(
        1
        for tf in tasks_data
        for task in tf.get("tasks", [])
        if task.get("module", "")
        in [
            "include_tasks",
            "import_tasks",
            "ansible.builtin.include_tasks",
            "ansible.builtin.import_tasks",
        ]
    )

    # Calculate max and average tasks per file
    tasks_per_file = [len(tf.get("tasks", [])) for tf in tasks_data]
    max_tasks_per_file = max(tasks_per_file) if tasks_per_file else 0
    avg_tasks_per_file = (
        sum(tasks_per_file) / len(tasks_per_file) if tasks_per_file else 0.0
    )

    # Detect external integrations
    integration_points = detect_integrations(role_info)

    # Analyze per-file complexity
    file_details = analyze_file_complexity(role_info, integration_points)

    # Detect conditional hotspots
    hotspots = detect_conditional_hotspots(role_info, file_details)

    # Detect inflection points
    inflection_points = detect_inflection_points(role_info, hotspots)

    # Create metrics
    metrics = ComplexityMetrics(
        total_tasks=total_tasks,
        task_files=task_files,
        handlers=handlers,
        conditional_tasks=conditional_tasks,
        error_handlers=error_handlers,
        role_dependencies=role_dependencies,
        role_includes=role_includes,
        task_includes=task_includes,
        external_integrations=len(integration_points),
        max_tasks_per_file=max_tasks_per_file,
        avg_tasks_per_file=avg_tasks_per_file,
    )

    # Classify complexity
    category = classify_complexity(metrics)

    # Extract repository info for linkable recommendations
    repository_url = role_info.get("repository")
    repo_type = role_info.get("repository_type")
    repo_branch = role_info.get("repository_branch")

    # Generate recommendations
    recommendations = generate_recommendations(
        metrics=metrics,
        category=category,
        integration_points=integration_points,
        inflection_points=inflection_points,
        file_details=file_details,
        hotspots=hotspots,
        role_info=role_info,
        repository_url=repository_url,
        repo_type=repo_type,
        repo_branch=repo_branch,
    )

    # Task files detail
    task_files_detail = [
        {
            "file": tf.get("file", "unknown"),
            "task_count": len(tf.get("tasks", [])),
            "has_integrations": _file_has_integrations(tf, integration_points),
        }
        for tf in tasks_data
    ]

    # Run pattern analysis if requested
    pattern_report = None
    if include_patterns and PATTERN_ANALYSIS_AVAILABLE:
        try:
            logger.info("Running pattern analysis...")
            pattern_report = analyze_role_patterns(
                role_info, min_confidence=min_confidence
            )
            logger.info(
                f"Pattern analysis complete: {pattern_report.total_patterns} patterns found "
                f"(health score: {pattern_report.overall_health_score:.1f}/100)"
            )
        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}", exc_info=True)
            pattern_report = None
    elif include_patterns and not PATTERN_ANALYSIS_AVAILABLE:
        logger.warning(
            "Pattern analysis requested but not available. "
            "Install pattern analyzer dependencies to enable this feature."
        )

    return ComplexityReport(
        metrics=metrics,
        category=category,
        integration_points=integration_points,
        recommendations=recommendations,
        task_files_detail=task_files_detail,
        pattern_analysis=pattern_report,
    )


def _file_has_integrations(
    task_file: dict[str, Any], integration_points: list[IntegrationPoint]
) -> int:
    """Count how many integration points a task file touches."""
    # Simple count for now - can be enhanced
    return 0
