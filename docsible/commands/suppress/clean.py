"""suppress clean — remove all expired rules."""

from pathlib import Path

import click

from docsible.suppression.store import load_store, resolve_suppress_path, save_store


@click.command(name="clean")
@click.option(
    "--path", "-p", "base_path", default=None,
    help="Base path for locating .docsible/suppress.yml",
)
@click.option(
    "--dry-run", is_flag=True, default=False,
    help="Show what would be removed without making changes",
)
def suppress_clean(base_path: str | None, dry_run: bool) -> None:
    """Remove all expired suppression rules.

    Rules with an --expires date in the past are considered expired.
    Rules with no expiry are never removed by this command.

    Example:

        docsible suppress clean
        docsible suppress clean --dry-run
    """
    suppress_path = resolve_suppress_path(Path(base_path) if base_path else None)
    store = load_store(suppress_path)
    expired = store.expired_rules()

    if not expired:
        click.echo("No expired rules to clean.")
        return

    if dry_run:
        click.echo(f"Would remove {len(expired)} expired rule(s):")
        for rule in expired:
            click.echo(f"  {rule.id}  {rule.pattern}  (expired {rule.expires_at})")
        return

    store.rules = store.active_rules()
    save_store(store, suppress_path)
    click.echo(f"✓ Removed {len(expired)} expired rule(s).")
