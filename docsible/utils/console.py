"""
Console output utilities for Docsible.

Provides colorized, formatted console output for reports and analysis.
"""

import logging
from typing import Optional

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
    report: ComplexityReport, role_name: Optional[str] = None
) -> None:
    """
    Display a formatted complexity analysis report to console.

    Args:
        report: ComplexityReport from analyze_role_complexity()
        role_name: Optional role name for display

    Example:
        >>> report = analyze_role_complexity(role_info)
        >>> display_complexity_report(report, "my_webserver_role")
    """
    metrics = report.metrics

    # Header
    print()
    print(f"{BOLD}{BLUE}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{BLUE}║         ROLE COMPLEXITY ANALYSIS                         ║{RESET}")
    print(f"{BOLD}{BLUE}╚══════════════════════════════════════════════════════════╝{RESET}")
    print()

    if role_name:
        print(f"{BOLD}Role:{RESET} {role_name}")
        print()

    # Metrics Section
    print(f"{BOLD}{CYAN}📊 Metrics:{RESET}")
    print(f"  Total Tasks:         {metrics.total_tasks}")
    print(f"  Task Files:          {metrics.task_files}")
    print(f"  Handlers:            {metrics.handlers}")
    print(
        f"  Conditional Tasks:   {metrics.conditional_tasks} ({metrics.conditional_percentage:.0f}% have conditions)"
    )

    if metrics.max_tasks_per_file > 0:
        print(f"  Max Tasks/File:      {metrics.max_tasks_per_file}")
        print(f"  Avg Tasks/File:      {metrics.avg_tasks_per_file:.1f}")
    print()

    # Role Composition Section
    print(f"{BOLD}{MAGENTA}📦 Role Composition (Internal Orchestration):{RESET}")
    print(f"  Role Dependencies:   {metrics.role_dependencies} (from meta/main.yml)")
    print(f"  Role Includes:       {metrics.role_includes} (include_role in tasks)")
    print(f"  Task Includes:       {metrics.task_includes} (include_tasks in tasks)")

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
    print(
        f"  Composition Score:   {composition_color}{composition_score} ({composition_level}){RESET}"
    )
    print()

    # External Integrations Section
    integration_count = len(report.integration_points)
    if integration_count > 0:
        print(
            f"{BOLD}{YELLOW}🔌 External Integrations ({integration_count} detected):{RESET}"
        )

        for idx, integration in enumerate(report.integration_points, 1):
            credential_icon = (
                " 🔑 Uses credentials" if integration.uses_credentials else ""
            )
            print(
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
            print(f"     {DIM}Modules: {modules_str}{RESET}")
        print()
    else:
        print(f"{BOLD}{GREEN}🔌 External Integrations:{RESET} None detected")
        print()

    # Complexity Category
    category_color = {
        ComplexityCategory.SIMPLE: GREEN,
        ComplexityCategory.MEDIUM: YELLOW,
        ComplexityCategory.COMPLEX: RED,
    }.get(report.category, RESET)

    print(
        f"{BOLD}🎯 Complexity:{RESET} {category_color}{BOLD}{report.category.value.upper()}{RESET}"
    )
    print()

    # Task Files Detail (if any)
    if report.task_files_detail and len(report.task_files_detail) > 0:
        print(f"{BOLD}{CYAN}📁 Task Files Breakdown:{RESET}")
        for tf in report.task_files_detail:
            file_name = tf.get("file", "unknown")
            task_count = tf.get("task_count", 0)
            print(f"  • {file_name}: {task_count} tasks")
        print()

    # Recommendations
    if report.recommendations:
        print(f"{BOLD}{BLUE}💡 Recommendations:{RESET}")
        for rec in report.recommendations:
            print(f"  • {rec}")
        print()

    # Summary line
    if report.category == ComplexityCategory.SIMPLE:
        print(f"{DIM}→ Recommended: Use sequence diagrams for visualization{RESET}")
    elif report.category == ComplexityCategory.MEDIUM:
        print(
            f"{DIM}→ Recommended: Use state transition + component tree diagrams{RESET}"
        )
    else:
        print(
            f"{DIM}→ Recommended: Use architecture diagrams + text documentation{RESET}"
        )

    print()
