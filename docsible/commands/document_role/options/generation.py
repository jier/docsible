"""Generation control CLI options for document_role command."""

from collections.abc import Callable
from typing import TypeVar

import click

F = TypeVar("F", bound=Callable[..., None])


def add_generation_options(f: F) -> F:
    """Add generation control options to the command.

    Args:
        f: Click command function to decorate

    Returns:
        Decorated command function with generation control options added

    Options:
    - --graph/-g: Generate Mermaid graph for tasks
    - --comments: Read comments from tasks files
    - --task-line: Read line numbers from tasks
    - --complexity-report: Show role complexity analysis
    - --simplification-report: Show anti-pattern detection and simplification suggestions
    - --show-dependencies: Generate task dependency matrix (for complex roles)
    - --analyze-only: Show complexity analysis without generating documentation
    """
    f = click.option(
        "--analyze-only",
        "analyze_only",
        is_flag=True,
        help="Analyze role complexity and display detailed metrics without generating documentation. "
        "Shows task counts, error handlers, dependencies, and integration points.",
    )(f)
    f = click.option(
        "--show-dependencies",
        "show_dependencies",
        is_flag=True,
        help="Generate task dependency matrix table in documentation. Shows variable dependencies, "
        "handler triggers, error handling strategies, and facts set by each task. "
        "Auto-enabled for complex roles with dependencies (smart defaults).",
    )(f)
    f = click.option(
        "--simplification-report",
        "simplification_report",
        is_flag=True,
        help="Include detailed pattern analysis with simplification suggestions in documentation. "
        "Detects anti-patterns across duplication, complexity, security, and maintainability "
        "categories. Provides actionable refactoring advice with code examples and impact assessment. "
        "Generates overall health score (0-100) and categorizes issues by severity (info/warning/critical).",
    )(f)
    f = click.option(
        "--complexity-report",
        "complexity_report",
        is_flag=True,
        help="Include role complexity analysis in generated documentation. Displays metrics like "
        "task counts, conditional tasks, error handlers, and external integrations with "
        "visualization strategy recommendations.",
    )(f)
    f = click.option(
        "--task-line",
        "-tl",
        "task_line",
        is_flag=True,
        help="Include source file line numbers for each task in generated documentation.",
    )(f)
    f = click.option(
        "--comments",
        "-com",
        "comments",
        is_flag=True,
        help="Extract and include inline comments from task files in documentation.",
    )(f)
    f = click.option(
        "--graph",
        "-g",
        "generate_graph",
        is_flag=True,
        help="Generate Mermaid diagrams for role visualization. Creates sequence diagrams, "
        "flowcharts, or architecture diagrams based on role complexity. "
        "Auto-enabled for medium/complex roles (smart defaults).",
    )(f)
    return f
