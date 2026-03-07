"""Suppression management command group."""

import click

from .add import suppress_add
from .clean import suppress_clean
from .list_ import suppress_list
from .remove import suppress_remove


@click.group(name="suppress")
def suppress_group() -> None:
    """Manage recommendation suppressions (silence false positives).

    Suppressions are stored in .docsible/suppress.yml relative to the
    role or working directory.

    Examples:

        docsible suppress add "no examples" --reason "Examples in separate repo"

        docsible suppress list

        docsible suppress remove abc123

        docsible suppress clean
    """


suppress_group.add_command(suppress_add, name="add")
suppress_group.add_command(suppress_list, name="list")
suppress_group.add_command(suppress_remove, name="remove")
suppress_group.add_command(suppress_clean, name="clean")

__all__ = ["suppress_group"]
