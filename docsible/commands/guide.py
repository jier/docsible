"""Guide command for interactive help and tutorials."""
import click
from pathlib import Path


GUIDES_DIR = Path(__file__).parent.parent / "help" / "guides"

AVAILABLE_TOPICS = ["getting-started", "troubleshooting", "smart-defaults"]


@click.command("guide")
@click.argument(
    "topic",
    type=click.Choice(AVAILABLE_TOPICS),
    metavar="TOPIC",
)
def guide_command(topic: str) -> None:
    """Show interactive guides and tutorials.

    TOPIC is one of: getting-started, troubleshooting, smart-defaults

    Examples:

        docsible guide getting-started

        docsible guide troubleshooting

        docsible guide smart-defaults
    """
    guide_path = GUIDES_DIR / f"{topic}.md"

    if not guide_path.exists():
        click.echo(f"Guide not found: {topic}", err=True)
        click.echo(f"Available guides: {', '.join(AVAILABLE_TOPICS)}")
        return

    content = guide_path.read_text()

    # Try rich for nice rendering, fall back to pager or plain
    try:
        from rich.console import Console
        from rich.markdown import Markdown

        console = Console()
        console.print(Markdown(content))
    except ImportError:
        # Fall back to click's pager or plain echo
        try:
            click.echo_via_pager(content)
        except Exception:
            click.echo(content)
