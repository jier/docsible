"""Inflection point detection (major branching points)."""

from typing import Any

from .models import InflectionPoint
from .hotspots import ConditionalHotspot


def detect_inflection_points(
    role_info: dict[str, Any], hotspots: list[ConditionalHotspot]
) -> list[InflectionPoint]:
    """Identify major branching points where execution paths diverge.

    An inflection point is a task that:
    1. Uses a conditional variable
    2. Is followed by many tasks using the same variable
    3. Represents a major decision point

    Args:
        role_info: Role information dictionary
        hotspots: Conditional hotspot analysis results

    Returns:
        List of InflectionPoint objects

    Example:
        >>> inflections = detect_inflection_points(role_info, hotspots)
        >>> for point in inflections:
        ...     print(f"{point.file_path}:{point.task_index} - {point.variable}")
    """
    inflection_points = []

    for hotspot in hotspots:
        # Find the task file
        task_file_info = next(
            (
                tf
                for tf in role_info.get("tasks", [])
                if tf.get("file") == hotspot.file_path
            ),
            None,
        )

        if not task_file_info:
            continue

        tasks = task_file_info.get("tasks", [])
        var_name = hotspot.conditional_variable

        # Find first task using this variable
        for idx, task in enumerate(tasks):
            when_clause = str(task.get("when", ""))

            if var_name in when_clause:
                # Count downstream tasks using same variable
                downstream = sum(
                    1 for t in tasks[idx + 1 :] if var_name in str(t.get("when", ""))
                )

                # Only report significant inflection points
                if downstream >= 3:
                    inflection_points.append(
                        InflectionPoint(
                            file_path=hotspot.file_path,
                            task_name=task.get("name", f"Task {idx + 1}"),
                            task_index=idx,
                            variable=var_name,
                            branch_count=2,  # Simplified: assume binary branch
                            downstream_tasks=downstream,
                        )
                    )
                    break  # Only report first major inflection per variable

    return inflection_points
