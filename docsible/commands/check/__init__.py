"""Check command for documentation drift detection."""

import click
from pathlib import Path
import sys


@click.command(name="check")
@click.option(
    "--role",
    "-r",
    "role_path",
    type=click.Path(exists=True),
    default=".",
    help="Path to Ansible role directory (default: current directory)",
)
@click.option(
    "--readme",
    type=click.Path(exists=True),
    default="README.md",
    help="Path to README file (default: README.md)",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Only output status (no details)",
)
def check(role_path, readme, quiet):
    """
    Check if role documentation is up to date.

    Exits with code 0 if documentation is current, 1 if outdated or missing.
    Useful for CI/CD pipelines to enforce documentation freshness.

    Examples:

        # Check current directory
        docsible check

        # Check specific role
        docsible check --role /path/to/role

        # Quiet mode (for scripts)
        docsible check --quiet && echo "Docs are fresh!"
    """
    from .core import check_documentation_drift

    is_fresh, details = check_documentation_drift(
        role_path=Path(role_path), readme_path=Path(readme)
    )

    if not quiet:
        if is_fresh:
            click.echo("✅ Documentation is up to date")
            if details.get("generated_at"):
                click.echo(f"   Last generated: {details['generated_at']}")
        else:
            click.echo("⚠️  Documentation is OUTDATED", err=True)
            click.echo("")
            if details.get("reason"):
                click.echo(f"   Reason: {details['reason']}", err=True)
            if details.get("changed_files"):
                click.echo(
                    f"   Changed files: {len(details['changed_files'])}", err=True
                )
                for file in details["changed_files"][:5]:
                    click.echo(f"     - {file}", err=True)
            if details.get("recommendation"):
                click.echo("", err=True)
                click.echo(f"   💡 {details['recommendation']}", err=True)

    sys.exit(0 if is_fresh else 1)
