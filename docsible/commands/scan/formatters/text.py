"""Text formatter for collection scan results."""

from __future__ import annotations

from docsible.commands.scan.models.scan_result import RoleResult, ScanCollectionResult


def _severity_sort_key(role: RoleResult) -> tuple[int, int, int]:
    """Sort key: critical desc, warnings desc, task_count desc."""
    return (-role.critical_count, -role.warning_count, -role.task_count)


def format_scan_text(result: ScanCollectionResult, top_n: int = 0) -> str:
    """Format collection scan results as a text table.

    Args:
        result: The aggregated scan result.
        top_n: If > 0, show only the top N worst roles (by severity).

    Returns:
        Formatted text output.
    """
    lines: list[str] = []

    lines.append(
        f"\nCollection scan: {result.collection_path}  ({result.total_roles} roles found)\n"
    )

    # Sort by severity: critical first, then warnings, then task count
    sorted_roles = sorted(result.roles, key=_severity_sort_key)

    if top_n > 0:
        sorted_roles = sorted_roles[:top_n]

    # Column widths
    name_width = max((len(r.name) for r in sorted_roles), default=4)
    name_width = max(name_width, len("Role"))

    header = (
        f"  {'Role':<{name_width}}   {'Complexity':<10}   {'Tasks':>5}   "
        f"{'Vars':>4}   {'Warnings':>8}   {'Critical':>8}"
    )
    separator = "  " + "\u2500" * (len(header) - 2)

    lines.append(header)
    lines.append(separator)

    for role in sorted_roles:
        complexity_label = role.complexity.capitalize() if role.complexity != "unknown" else "?"
        lines.append(
            f"  {role.name:<{name_width}}   {complexity_label:<10}   {role.task_count:>5}   "
            f"{role.variable_count:>4}   {role.warning_count:>8}   {role.critical_count:>8}"
        )

    lines.append("")

    # Summary line
    need_attention = len([r for r in result.roles if r.warning_count > 0 or r.critical_count > 0])
    critical_roles = len(result.roles_with_critical)

    if critical_roles > 0:
        critical_part = f" | {critical_roles} critical finding{'s' if critical_roles != 1 else ''}"
    else:
        critical_part = ""

    lines.append(
        f"  Summary: {result.total_roles} role{'s' if result.total_roles != 1 else ''}"
        f" | {need_attention} need attention{critical_part}"
    )
    lines.append("  Run with --advanced-patterns for full findings per role.")
    lines.append("")

    return "\n".join(lines)
