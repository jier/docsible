"""Tests for the 'suppress clean' CLI command."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml
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


def load_yaml_rules(tmp_path: Path) -> list[dict]:
    path = tmp_path / ".docsible" / "suppress.yml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("rules", [])  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_suppress_clean_removes_expired_rules(tmp_path):
    past = datetime.now(timezone.utc) - timedelta(days=1)
    future = datetime.now(timezone.utc) + timedelta(days=30)
    expired = make_rule(id="expred01", expires_at=past)
    active = make_rule(id="active01", expires_at=future)
    save_rules_to(tmp_path, [expired, active])

    result = invoke(["clean", "--path", str(tmp_path)])
    assert result.exit_code == 0

    rules = load_yaml_rules(tmp_path)
    ids = {r["id"] for r in rules}
    assert "expred01" not in ids
    assert "active01" in ids


def test_suppress_clean_dry_run_does_not_remove(tmp_path):
    past = datetime.now(timezone.utc) - timedelta(days=1)
    expired = make_rule(id="expred01", expires_at=past)
    save_rules_to(tmp_path, [expired])

    invoke(["clean", "--dry-run", "--path", str(tmp_path)])

    rules = load_yaml_rules(tmp_path)
    ids = {r["id"] for r in rules}
    assert "expred01" in ids


def test_suppress_clean_no_expired_rules(tmp_path):
    result = invoke(["clean", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "No expired rules to clean." in result.output
