"""Tests for the 'suppress add' CLI command."""

from pathlib import Path

import yaml
from click.testing import CliRunner

from docsible.commands.suppress import suppress_group

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def invoke(args: list[str]):
    runner = CliRunner()
    return runner.invoke(suppress_group, args, catch_exceptions=False)


def load_yaml_rules(tmp_path: Path) -> list[dict]:
    path = tmp_path / ".docsible" / "suppress.yml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("rules", [])  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_suppress_add_creates_rule(tmp_path):
    result = invoke(["add", "no examples", "--reason", "Legacy role",
                     "--path", str(tmp_path)])
    assert result.exit_code == 0, result.output
    rules = load_yaml_rules(tmp_path)
    assert len(rules) == 1
    assert rules[0]["pattern"] == "no examples"
    assert rules[0]["reason"] == "Legacy role"


def test_suppress_add_with_expiry(tmp_path):
    result = invoke(["add", "no examples", "--reason", "Temp",
                     "--expires", "30", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.output
    rules = load_yaml_rules(tmp_path)
    assert rules[0]["expires_at"] is not None


def test_suppress_add_with_file_glob(tmp_path):
    result = invoke(["add", "no examples", "--reason", "Scoped",
                     "--file", "roles/*", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.output
    rules = load_yaml_rules(tmp_path)
    assert rules[0]["file_pattern"] == "roles/*"


def test_suppress_add_with_regex(tmp_path):
    result = invoke(["add", r"no\s+example", "--reason", "Regex rule",
                     "--regex", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.output
    rules = load_yaml_rules(tmp_path)
    assert rules[0]["use_regex"] is True
