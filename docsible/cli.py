"""Docsible CLI - Ansible role and collection documentation generator.

This is the main entry point for the Docsible command-line interface.
It sets up the Click command group and registers all available commands.
"""

import logging
import sys

import click

from docsible.commands.document_role import doc_the_role
from docsible.commands.init_config import init_config
from docsible.commands.check import check

# Setup logging
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Args:
        verbose: If True, set log level to DEBUG, otherwise INFO

    Example:
        >>> setup_logging(verbose=True)
        >>> logger.debug("This will be shown")
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_version() -> str:
    """Get the current version of docsible.

    Tries to get version from git tags first, falls back to constants.

    Returns:
        Version string (e.g., "0.8.0" or "0.8.0.dev5+gabc1234" if in development)

    Example:
        >>> version = get_version()
        >>> print(f"Docsible v{version}")
        Docsible v0.8.0
    """
    from docsible.utils.version import get_version as get_dynamic_version
    return get_dynamic_version()


@click.group()
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose logging (DEBUG level)"
)
@click.version_option(
    version=get_version(),
    help=f"Show the module version. Current version: {get_version()}",
)
def cli(verbose: bool):
    """Docsible - Ansible role and collection documentation generator.

    Generate comprehensive documentation for your Ansible roles and collections
    with support for Mermaid diagrams, variable documentation, and more.

    Use 'docsible COMMAND --help' for more information on a specific command.

    Examples:
        docsible role --role ./my-role --graph
        docsible init --path ./my-role
        docsible role --role ./my-role  --check
    """
    setup_logging(verbose)
    logger.debug("Docsible CLI started")


# Register commands
cli.add_command(doc_the_role, name="role")
cli.add_command(init_config, name="init")
cli.add_command(check)


def main():
    """Main entry point for the CLI application.

    This function is called when docsible is invoked from the command line.
    It ensures logging is set up and the CLI group is invoked.
    """
    cli()


if __name__ == "__main__":
    main()
