"""JSON formatter for collection scan results."""

from __future__ import annotations

import json

from docsible.commands.scan.models.scan_result import ScanCollectionResult


def format_scan_json(result: ScanCollectionResult, top_n: int = 0) -> str:
    """Format collection scan results as JSON.

    Args:
        result: The aggregated scan result.
        top_n: If > 0, include only the top N worst roles (by severity).

    Returns:
        JSON-formatted string.
    """
    complexity_breakdown: dict[str, int] = {}
    for role in result.roles:
        key = role.complexity if role.complexity else "unknown"
        complexity_breakdown[key] = complexity_breakdown.get(key, 0) + 1

    roles_data = sorted(
        result.roles,
        key=lambda r: (-r.critical_count, -r.warning_count, -r.task_count),
    )
    if top_n > 0:
        roles_data = roles_data[:top_n]

    collection_path = result.collection_path
    roles_list = []
    for role in roles_data:
        # Make role path relative to collection path when possible
        try:
            rel_path = role.path.relative_to(collection_path)
            path_str = str(rel_path)
        except ValueError:
            path_str = str(role.path)

        roles_list.append(
            {
                "name": role.name,
                "path": path_str,
                "task_count": role.task_count,
                "variable_count": role.variable_count,
                "complexity": role.complexity,
                "critical_count": role.critical_count,
                "warning_count": role.warning_count,
                "info_count": role.info_count,
                "top_recommendations": role.top_recommendations,
                **({"error": role.error} if role.error else {}),
            }
        )

    output = {
        "collection_path": str(collection_path),
        "total_roles": result.total_roles,
        "summary": {
            "total_critical": result.total_critical,
            "total_warnings": result.total_warnings,
            "complexity_breakdown": complexity_breakdown,
        },
        "roles": roles_list,
    }

    return json.dumps(output, indent=2)
