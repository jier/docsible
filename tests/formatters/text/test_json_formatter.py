"""Tests for JsonRecommendationFormatter."""
import json

import pytest

from docsible.formatters.text.json_formatter import JsonRecommendationFormatter
from docsible.models.recommendation import Recommendation
from docsible.models.severity import Severity


@pytest.fixture
def critical_rec() -> Recommendation:
    return Recommendation(
        category="security",
        message="Vault file not encrypted",
        rationale="Unencrypted vault files expose secrets",
        severity=Severity.CRITICAL,
        file_path="vars/vault.yml",
        line_number=1,
        remediation="Run: ansible-vault encrypt vault.yml",
        confidence=1.0,
        auto_fixable=False,
    )


@pytest.fixture
def warning_rec() -> Recommendation:
    return Recommendation(
        category="documentation",
        message="Complex role lacks task descriptions",
        rationale="Large roles need documentation",
        severity=Severity.WARNING,
        file_path="tasks/main.yml",
        line_number=None,
        remediation="Add comments above tasks",
        confidence=0.9,
        auto_fixable=False,
    )


@pytest.fixture
def info_rec() -> Recommendation:
    return Recommendation(
        category="best_practices",
        message="Consider adding examples/ directory",
        rationale="Example playbooks help users",
        severity=Severity.INFO,
        file_path=None,
        line_number=None,
        remediation="Create examples/ with sample playbook.yml",
        confidence=0.6,
        auto_fixable=False,
    )


@pytest.fixture
def mixed_recs(critical_rec, warning_rec, info_rec) -> list[Recommendation]:
    return [critical_rec, warning_rec, info_rec]


class TestJsonRecommendationFormatter:
    """Tests for JsonRecommendationFormatter."""

    def test_output_is_valid_json(self, mixed_recs):
        """Output must be parseable JSON."""
        formatter = JsonRecommendationFormatter()
        output = formatter.format(mixed_recs, role_name="my_role")
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_findings_list_has_correct_shape(self, critical_rec):
        """Each finding must have the expected keys."""
        formatter = JsonRecommendationFormatter()
        output = formatter.format([critical_rec], role_name="test_role")
        parsed = json.loads(output)

        assert "findings" in parsed
        assert len(parsed["findings"]) == 1

        finding = parsed["findings"][0]
        expected_keys = {
            "severity", "category", "message", "rationale",
            "file", "line", "remediation", "confidence", "auto_fixable",
        }
        assert expected_keys == set(finding.keys())

    def test_finding_values_match_recommendation(self, critical_rec):
        """Finding values must match the source Recommendation."""
        formatter = JsonRecommendationFormatter()
        output = formatter.format([critical_rec])
        parsed = json.loads(output)

        finding = parsed["findings"][0]
        assert finding["severity"] == "critical"
        assert finding["category"] == "security"
        assert finding["message"] == "Vault file not encrypted"
        assert finding["file"] == "vars/vault.yml"
        assert finding["line"] == 1
        assert finding["confidence"] == 1.0
        assert finding["auto_fixable"] is False

    def test_summary_counts_match(self, mixed_recs):
        """Summary counts must reflect actual severities."""
        formatter = JsonRecommendationFormatter()
        output = formatter.format(mixed_recs, role_name="my_role")
        parsed = json.loads(output)

        summary = parsed["summary"]
        assert summary["critical"] == 1
        assert summary["warning"] == 1
        assert summary["info"] == 1
        assert summary["shown"] == 3
        assert summary["total"] == 3

    def test_summary_total_uses_total_count_when_provided(self, warning_rec):
        """When total_count is given, summary.total should use it (truncated scenario)."""
        formatter = JsonRecommendationFormatter()
        output = formatter.format([warning_rec], role_name="my_role", truncated=True, total_count=10)
        parsed = json.loads(output)

        summary = parsed["summary"]
        assert summary["total"] == 10
        assert summary["shown"] == 1

    def test_truncated_flag_false_by_default(self, mixed_recs):
        """truncated must be False when not specified."""
        formatter = JsonRecommendationFormatter()
        output = formatter.format(mixed_recs)
        parsed = json.loads(output)
        assert parsed["truncated"] is False

    def test_truncated_flag_true_when_set(self, mixed_recs):
        """truncated must reflect the argument."""
        formatter = JsonRecommendationFormatter()
        output = formatter.format(mixed_recs, truncated=True, total_count=20)
        parsed = json.loads(output)
        assert parsed["truncated"] is True

    def test_role_name_in_output(self, critical_rec):
        """role field must match provided role_name."""
        formatter = JsonRecommendationFormatter()
        output = formatter.format([critical_rec], role_name="nginx_role")
        parsed = json.loads(output)
        assert parsed["role"] == "nginx_role"

    def test_empty_recommendations(self):
        """Empty list should produce valid JSON with zero counts."""
        formatter = JsonRecommendationFormatter()
        output = formatter.format([])
        parsed = json.loads(output)

        assert parsed["findings"] == []
        assert parsed["summary"]["total"] == 0
        assert parsed["summary"]["shown"] == 0
        assert parsed["summary"]["critical"] == 0
        assert parsed["summary"]["warning"] == 0
        assert parsed["summary"]["info"] == 0

    def test_missing_file_path_becomes_empty_string(self, info_rec):
        """file_path=None in Recommendation should become empty string in JSON."""
        formatter = JsonRecommendationFormatter()
        output = formatter.format([info_rec])
        parsed = json.loads(output)

        finding = parsed["findings"][0]
        assert finding["file"] == ""

    def test_missing_remediation_becomes_empty_string(self):
        """remediation=None should become empty string in JSON."""
        rec = Recommendation(
            category="testing",
            message="No tests found",
            rationale="Tests prevent regressions",
            severity=Severity.INFO,
            confidence=0.7,
        )
        formatter = JsonRecommendationFormatter()
        output = formatter.format([rec])
        parsed = json.loads(output)

        finding = parsed["findings"][0]
        assert finding["remediation"] == ""
