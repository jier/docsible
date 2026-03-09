"""suppress list — display all suppression rules."""

from pathlib import Path

import click

from docsible.suppression.store import load_store, resolve_suppress_path


@click.command(name="list")
@click.option(
    "--path",
    "-p",
    "base_path",
    default=None,
    help="Base path for locating .docsible/suppress.yml",
)
@click.option(
    "--show-expired",
    is_flag=True,
    default=False,
    help="Include expired rules in the listing",
)
def suppress_list(base_path: str | None, show_expired: bool) -> None:
    """List all suppression rules.

    Active rules are shown by default. Use --show-expired to include expired rules.
    """
    suppress_path = resolve_suppress_path(Path(base_path) if base_path else None)
    store = load_store(suppress_path)

    rules = store.rules if show_expired else store.active_rules()

    if not rules:
        click.echo("No suppression rules found.")
        expired = store.expired_rules()
        if not show_expired and expired:
            click.echo(f"  ({len(expired)} expired rule(s) hidden — use --show-expired)")
        return

    click.echo(f"\nSuppression rules ({suppress_path}):\n")
    click.echo(f"{'ID':<10} {'PATTERN':<30} {'MATCHES':<8} {'EXPIRES':<12} REASON")
    click.echo("-" * 80)

    for rule in rules:
        expired_tag = " [EXPIRED]" if rule.is_expired() else ""
        expires_str = rule.expires_at.strftime("%Y-%m-%d") if rule.expires_at else "never"
        pattern_display = rule.pattern[:28] + ".." if len(rule.pattern) > 30 else rule.pattern
        reason_display = rule.reason[:30] + ".." if len(rule.reason) > 32 else rule.reason
        click.echo(
            f"{rule.id:<10} {pattern_display:<30} {rule.match_count:<8} "
            f"{expires_str:<12} {reason_display}{expired_tag}"
        )

    click.echo()
    active_count = len(store.active_rules())
    expired_count = len(store.expired_rules())
    click.echo(f"Total: {active_count} active, {expired_count} expired")
