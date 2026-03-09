"""Tests for SuppressionRule and SuppressionStore pydantic models."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from docsible.models.suppression import SuppressionRule, SuppressionStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_rule(**kwargs) -> SuppressionRule:
    defaults = {
        "id": "abc12345",
        "pattern": "no examples",
        "reason": "Examples live in separate repo",
    }
    defaults.update(kwargs)
    return SuppressionRule(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# SuppressionRule — validators
# ---------------------------------------------------------------------------


def test_rule_requires_non_empty_pattern():
    with pytest.raises(ValidationError, match="pattern must not be empty"):
        make_rule(pattern="")


def test_rule_requires_non_empty_reason():
    with pytest.raises(ValidationError, match="reason must not be empty"):
        make_rule(reason="")


# ---------------------------------------------------------------------------
# SuppressionRule.is_expired()
# ---------------------------------------------------------------------------


def test_rule_not_expired_when_expires_at_none():
    rule = make_rule(expires_at=None)
    assert rule.is_expired() is False


def test_rule_expired_when_expires_at_in_past():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    rule = make_rule(expires_at=past)
    assert rule.is_expired() is True


def test_rule_not_expired_when_expires_at_in_future():
    future = datetime.now(timezone.utc) + timedelta(days=30)
    rule = make_rule(expires_at=future)
    assert rule.is_expired() is False


# ---------------------------------------------------------------------------
# SuppressionRule.matches_message()
# ---------------------------------------------------------------------------


def test_matches_message_substring_case_insensitive():
    rule = make_rule(pattern="no examples")
    assert rule.matches_message("Role has NO EXAMPLES section") is True


def test_matches_message_regex():
    rule = make_rule(pattern=r"no\s+example", use_regex=True)
    assert rule.matches_message("Role has no   example blocks") is True


# ---------------------------------------------------------------------------
# SuppressionRule.matches_file()
# ---------------------------------------------------------------------------


def test_matches_file_none_pattern_matches_all():
    rule = make_rule(file_pattern=None)
    assert rule.matches_file("roles/webserver/tasks/main.yml") is True
    assert rule.matches_file(None) is True
    assert rule.matches_file("any/path.yml") is True


def test_matches_file_glob_pattern():
    rule = make_rule(file_pattern="roles/*")
    assert rule.matches_file("roles/webserver") is True
    assert rule.matches_file("collections/myns/role") is False


# ---------------------------------------------------------------------------
# SuppressionStore
# ---------------------------------------------------------------------------


def test_store_active_rules_excludes_expired():
    past = datetime.now(timezone.utc) - timedelta(days=1)
    future = datetime.now(timezone.utc) + timedelta(days=1)
    expired = make_rule(id="exp00001", expires_at=past)
    active = make_rule(id="act00001", expires_at=future)
    store = SuppressionStore(rules=[expired, active])
    active_ids = {r.id for r in store.active_rules()}
    assert "exp00001" not in active_ids
    assert "act00001" in active_ids


def test_store_remove_by_id_success():
    rule1 = make_rule(id="id000001")
    rule2 = make_rule(id="id000002")
    store = SuppressionStore(rules=[rule1, rule2])
    result = store.remove_by_id("id000001")
    assert result is True
    assert len(store.rules) == 1
    assert store.rules[0].id == "id000002"


def test_store_remove_by_id_nonexistent():
    rule = make_rule(id="id000001")
    store = SuppressionStore(rules=[rule])
    result = store.remove_by_id("doesntexist")
    assert result is False
    assert len(store.rules) == 1
