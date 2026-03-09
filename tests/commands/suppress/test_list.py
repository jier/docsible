"""Tests for the 'suppress list' CLI command."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from click.testing import CliRunner

from docsible.commands.suppress import suppress_group
from docsible.models.suppression import SuppressionRule, SuppressionStore
from docsible.suppression.store import save_store

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_rule(**kwargs) -> SuppressionRule:
    defaults = {
        "id": "abc12345",
        "pattern": "no examples",
        "reason": "Examples in separate repo",
    }
    defaults.update(kwargs)
    return SuppressionRule(**defaults)  # type: ignore[arg-type]


def invoke(args: list[str]):
    runner = CliRunner()
    return runner.invoke(suppress_group, args, catch_exceptions=False)


def save_rules_to(tmp_path: Path, rules: list[SuppressionRule]) -> Path:
    path = tmp_path / ".docsible" / "suppress.yml"
    store = SuppressionStore(rules=rules)
    save_store(store, path)
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_suppress_list_empty(tmp_path):
    result = invoke(["list", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "No suppression rules found." in result.output


def test_suppress_list_shows_active_rules(tmp_path):
    rule = make_rule(id="abc12345", pattern="no examples", reason="Legacy")
    save_rules_to(tmp_path, [rule])
    result = invoke(["list", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "abc12345" in result.output
    assert "no examples" in result.output


def test_suppress_list_show_expired_includes_expired(tmp_path):
    past = datetime.now(timezone.utc) - timedelta(days=1)
    expired = make_rule(id="expred01", pattern="expired pattern", expires_at=past)
    save_rules_to(tmp_path, [expired])
    result = invoke(["list", "--show-expired", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "expred01" in result.output
    assert "expired pattern" in result.output
