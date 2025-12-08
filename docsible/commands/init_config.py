"""Command for initializing Docsible configuration."""

import logging
from pathlib import Path

import click

from docsible.utils.project_structure import create_example_config

logger = logging.getLogger(__name__)


@click.command(name="init")
@click.option("--path", "-p", default=".", help="Path where to create .docsible.yml")
@click.option(
    "--force", "-f", is_flag=True, help="Overwrite existing .docsible.yml file"
)
def init_config(path: str, force: bool):
    """Generate an example .docsible.yml configuration file.

    This file allows you to customize how docsible interprets your
    Ansible project structure. The configuration file defines:

    - Directory names for defaults, vars, tasks, meta, handlers, etc.
    - File naming conventions
    - Project-specific structure customizations

    Example:
        docsible init --path ./my-role
        docsible init --path . --force
    """
    config_path = Path(path) / ".docsible.yml"

    if config_path.exists() and not force:
        click.echo(f"❌ Configuration file already exists at {config_path}")
        raise click.ClickException("Configuration file already exists. Use --force to overwrite.")

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(create_example_config())

        click.echo(f"✓ Example configuration created at: {config_path}")
        click.echo("\nYou can now customize this file to match your project structure.")
        logger.info(f"Created config file: {config_path}")

    except Exception as e:
        click.echo(f"❌ Failed to create configuration file: {e}")
        logger.error(f"Failed to create config: {e}")
        raise click.ClickException(str(e))
