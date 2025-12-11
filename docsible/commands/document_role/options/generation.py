"""Generation control CLI options for document_role command."""
import click


def add_generation_options(f):
    """Add generation control options to the command.

    Options:
    - --graph/-g: Generate Mermaid graph for tasks
    - --comments: Read comments from tasks files
    - --task-line: Read line numbers from tasks
    - --complexity-report: Show role complexity analysis
    """
    f = click.option("--complexity-report", "complexity_report", is_flag=True,
                     help="Show role complexity analysis before generating documentation.")(f)
    f = click.option("--task-line", "-tl", "task_line", is_flag=True,
                     help="Read line numbers from tasks")(f)
    f = click.option("--comments", "-com", "comments", is_flag=True,
                     help="Read comments from tasks files")(f)
    f = click.option("--graph", "-g", "generate_graph", is_flag=True,
                     help="Generate Mermaid graph for tasks.")(f)
    return f
