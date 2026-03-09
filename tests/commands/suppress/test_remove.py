"""Tests for the 'suppress remove' CLI command."""

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


def test_suppress_remove_existing_id(tmp_path):
    rule = make_rule(id="abc12345")
    save_rules_to(tmp_path, [rule])

    result = invoke(["remove", "abc12345", "--path", str(tmp_path)])
    assert result.exit_code == 0

    rules = load_yaml_rules(tmp_path)
    assert all(r["id"] != "abc12345" for r in rules)


def test_suppress_remove_nonexistent_id(tmp_path):
    save_rules_to(tmp_path, [])

    runner = CliRunner()
    result = runner.invoke(suppress_group,
                           ["remove", "doesntex", "--path", str(tmp_path)],
                           catch_exceptions=False)
    assert result.exit_code != 0
