"""suppress remove — delete a rule by ID."""

from pathlib import Path

import click

from docsible.suppression.store import load_store, resolve_suppress_path, save_store


@click.command(name="remove")
@click.argument("rule_id")
@click.option(
    "--path", "-p", "base_path", default=None,
    help="Base path for locating .docsible/suppress.yml",
)
def suppress_remove(rule_id: str, base_path: str | None) -> None:
    """Remove a suppression rule by its ID.

    RULE_ID is the 8-character identifier shown in 'suppress list'.

    Example:

        docsible suppress remove abc123
    """
    suppress_path = resolve_suppress_path(Path(base_path) if base_path else None)
    store = load_store(suppress_path)

    removed = store.remove_by_id(rule_id)
    if not removed:
        raise click.ClickException(f"No rule found with ID: {rule_id}")

    save_store(store, suppress_path)
    click.echo(f"✓ Suppression rule {rule_id} removed.")
