"""Generation control CLI options for document_role command."""

import click


def add_generation_options(f):
    """Add generation control options to the command.

    Options:
    - --graph/-g: Generate Mermaid graph for tasks
    - --comments: Read comments from tasks files
    - --task-line: Read line numbers from tasks
    - --complexity-report: Show role complexity analysis
    - --show-dependencies: Generate task dependency matrix (for complex roles)
    - --analyze-only: Show complexity analysis without generating documentation
    """
    f = click.option(
        "--analyze-only",
        "analyze_only",
        is_flag=True,
        help="Analyze role complexity and show report without generating documentation.",
    )(f)
    f = click.option(
        "--show-dependencies",
        "show_dependencies",
        is_flag=True,
        help="Generate task dependency matrix showing relationships, triggers, and error handling.",
    )(f)
    f = click.option(
        "--complexity-report",
        "complexity_report",
        is_flag=True,
        help="Show role complexity analysis before generating documentation.",
    )(f)
    f = click.option(
        "--task-line",
        "-tl",
        "task_line",
        is_flag=True,
        help="Read line numbers from tasks",
    )(f)
    f = click.option(
        "--comments",
        "-com",
        "comments",
        is_flag=True,
        help="Read comments from tasks files",
    )(f)
    f = click.option(
        "--graph",
        "-g",
        "generate_graph",
        is_flag=True,
        help="Generate Mermaid graph for tasks.",
    )(f)
    return f
