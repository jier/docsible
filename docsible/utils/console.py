"""
Console output utilities for Docsible.

Provides colorized, formatted console output for reports and analysis.
"""

import logging

import click

from docsible.analyzers import ComplexityCategory, ComplexityReport

logger = logging.getLogger(__name__)

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Colors
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"


def display_complexity_report(
    report: ComplexityReport, role_name: str | None = None, quiet: bool = False
) -> None:
    """
    Display a formatted complexity analysis report to console.

    Args:
        report: ComplexityReport from analyze_role_complexity()
        role_name: Optional role name for display
        quiet: If True, suppress output (for programmatic use)

    Example:
        >>> report = analyze_role_complexity(role_info)
        >>> display_complexity_report(report, "my_webserver_role")
    """
    if quiet:
        return

    metrics = report.metrics

    # Header
    click.echo()
    click.echo(f"{BOLD}{BLUE}╔══════════════════════════════════════════════════════════╗{RESET}")
    click.echo(f"{BOLD}{BLUE}║         ROLE COMPLEXITY ANALYSIS                         ║{RESET}")
    click.echo(f"{BOLD}{BLUE}╚══════════════════════════════════════════════════════════╝{RESET}")
    click.echo()

    if role_name:
        click.echo(f"{BOLD}Role:{RESET} {role_name}")
        click.echo()

    # Metrics Section
    click.echo(f"{BOLD}{CYAN}📊 Metrics:{RESET}")
    click.echo(f"  Total Tasks:         {metrics.total_tasks}")
    click.echo(f"  Task Files:          {metrics.task_files}")
    click.echo(f"  Handlers:            {metrics.handlers}")
    click.echo(
        f"  Conditional Tasks:   {metrics.conditional_tasks} ({metrics.conditional_percentage:.0f}% have conditions)"
    )

    if metrics.max_tasks_per_file > 0:
        click.echo(f"  Max Tasks/File:      {metrics.max_tasks_per_file}")
        click.echo(f"  Avg Tasks/File:      {metrics.avg_tasks_per_file:.1f}")
    click.echo()

    # Role Composition Section
    click.echo(f"{BOLD}{MAGENTA}📦 Role Composition (Internal Orchestration):{RESET}")
    click.echo(f"  Role Dependencies:   {metrics.role_dependencies} (from meta/main.yml)")
    click.echo(f"  Role Includes:       {metrics.role_includes} (include_role in tasks)")
    click.echo(f"  Task Includes:       {metrics.task_includes} (include_tasks in tasks)")

    composition_score = metrics.composition_score
    composition_level = (
        "Low"
        if composition_score < 4
        else "Medium"
        if composition_score < 8
        else "High"
    )
    composition_color = (
        GREEN if composition_score < 4 else YELLOW if composition_score < 8 else RED
    )
    click.echo(
        f"  Composition Score:   {composition_color}{composition_score} ({composition_level}){RESET}"
    )
    click.echo()

    # External Integrations Section
    integration_count = len(report.integration_points)
    if integration_count > 0:
        click.echo(
            f"{BOLD}{YELLOW}🔌 External Integrations ({integration_count} detected):{RESET}"
        )

        for idx, integration in enumerate(report.integration_points, 1):
            credential_icon = (
                " 🔑 Uses credentials" if integration.uses_credentials else ""
            )
            click.echo(
                f"  {idx}. {integration.system_name} ({integration.task_count} tasks){credential_icon}"
            )

            # Show modules used (limit to 3 for brevity)
            if len(integration.modules_used) <= 3:
                modules_str = ", ".join(integration.modules_used)
            else:
                modules_str = (
                    ", ".join(integration.modules_used[:3])
                    + f" (+{len(integration.modules_used) - 3} more)"
                )
            click.echo(f"     {DIM}Modules: {modules_str}{RESET}")
        click.echo()
    else:
        click.echo(f"{BOLD}{GREEN}🔌 External Integrations:{RESET} None detected")
        click.echo()

    # Complexity Category
    category_color = {
        ComplexityCategory.SIMPLE: GREEN,
        ComplexityCategory.MEDIUM: YELLOW,
        ComplexityCategory.COMPLEX: RED,
    }.get(report.category, RESET)

    click.echo(
        f"{BOLD}🎯 Complexity:{RESET} {category_color}{BOLD}{report.category.value.upper()}{RESET}"
    )
    click.echo()

    # Task Files Detail (if any)
    if report.task_files_detail and len(report.task_files_detail) > 0:
        click.echo(f"{BOLD}{CYAN}📁 Task Files Breakdown:{RESET}")
        for tf in report.task_files_detail:
            file_name = tf.get("file", "unknown")
            task_count = tf.get("task_count", 0)
            click.echo(f"  • {file_name}: {task_count} tasks")
        click.echo()

    # Recommendations
    if report.recommendations:
        click.echo(f"{BOLD}{BLUE}💡 Recommendations:{RESET}")
        for rec in report.recommendations:
            click.echo(f"  • {rec}")
        click.echo()

    # Summary line
    if report.category == ComplexityCategory.SIMPLE:
        click.echo(f"{DIM}→ Recommended: Use sequence diagrams for visualization{RESET}")
    elif report.category == ComplexityCategory.MEDIUM:
        click.echo(
            f"{DIM}→ Recommended: Use state transition + component tree diagrams{RESET}"
        )
    else:
        click.echo(
            f"{DIM}→ Recommended: Use architecture diagrams + text documentation{RESET}"
        )

    click.echo()
