"""suppress add — create a new suppression rule."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import click

from docsible.models.suppression import SuppressionRule
from docsible.suppression.id_gen import generate_rule_id
from docsible.suppression.store import load_store, resolve_suppress_path, save_store


@click.command(name="add")
@click.argument("pattern")
@click.option("--reason", "-r", required=True, help="Justification for suppression")
@click.option(
    "--file",
    "-f",
    "file_pattern",
    default=None,
    help="Scope to files matching this glob pattern (e.g., 'roles/webserver')",
)
@click.option(
    "--expires",
    "-e",
    "expires_days",
    default=None,
    type=int,
    help="Auto-expire after N days (omit for no expiry)",
)
@click.option("--approved-by", default=None, help="Name of approver (for audit trail)")
@click.option(
    "--regex",
    is_flag=True,
    default=False,
    help="Treat PATTERN as a regular expression instead of a substring",
)
@click.option(
    "--path",
    "-p",
    "base_path",
    default=None,
    help="Base path for locating .docsible/suppress.yml (default: current directory)",
)
def suppress_add(
    pattern: str,
    reason: str,
    file_pattern: str | None,
    expires_days: int | None,
    approved_by: str | None,
    regex: bool,
    base_path: str | None,
) -> None:
    """Add a new suppression rule for PATTERN.

    PATTERN is a case-insensitive substring matched against recommendation
    messages. Use --regex to treat it as a full regular expression.

    Examples:

        docsible suppress add "no examples" --reason "Examples in separate repo"

        docsible suppress add "no examples" --reason "Legacy role" --expires 90

        docsible suppress add "no examples" --reason "Legacy" --file "roles/webserver"
    """
    expires_at = None
    if expires_days is not None:
        if expires_days <= 0:
            raise click.BadParameter("must be a positive integer", param_hint="--expires")
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

    rule_id = generate_rule_id(pattern)

    rule = SuppressionRule(
        id=rule_id,
        pattern=pattern,
        reason=reason,
        file_pattern=file_pattern,
        expires_at=expires_at,
        approved_by=approved_by,
        use_regex=regex,
    )

    suppress_path = resolve_suppress_path(Path(base_path) if base_path else None)
    store = load_store(suppress_path)
    store.rules.append(rule)
    save_store(store, suppress_path)

    click.echo(f"✓ Suppression rule added: {rule_id}")
    click.echo(f"  Pattern : {pattern}")
    click.echo(f"  Reason  : {reason}")
    if file_pattern:
        click.echo(f"  Scope   : {file_pattern}")
    if expires_at:
        click.echo(f"  Expires : {expires_at.strftime('%Y-%m-%d')}")
    click.echo(f"  Stored  : {suppress_path}")
