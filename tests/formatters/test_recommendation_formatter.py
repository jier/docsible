import pytest

from docsible.formatters.recommendation_formatter import RecommendationFormatter
from docsible.models.recommendation import Recommendation
from docsible.models.severity import Severity


@pytest.fixture
def security_recommendations() -> list[Recommendation]:
    """Mock security recommendations (CRITICAL severity)."""
    return [
        Recommendation(
            category="security",
            message="Vault file not encrypted: vault.yml",
            rationale="Unencrypted vault files expose secrets in version control",
            severity=Severity.CRITICAL,
            file_path="vars/vault.yml",
            line_number=1,
            remediation="Run: ansible-vault encrypt vault.yml",
            confidence=1.0,
            auto_fixable=False,
        ),
        Recommendation(
            category="security",
            message="Potentially sensitive variable exposed in debug: db_password",
            rationale="Debug output may expose secrets in logs",
            severity=Severity.CRITICAL,
            file_path="tasks/main.yml",
            line_number=42,
            remediation="Use no_log: true or remove debug statement",
            confidence=0.8,
            auto_fixable=False,
        ),
        Recommendation(
            category="security",
            message="Unsafe file permissions detected: mode=0777",
            rationale="World-writable permissions (777/666) are a security risk",
            severity=Severity.CRITICAL,
            file_path="tasks/deploy.yml",
            line_number=15,
            remediation="Use restrictive permissions like 0644 or 0755",
            confidence=0.95,
            auto_fixable=False,
        ),
    ]


@pytest.fixture
def quality_recommendations() -> list[Recommendation]:
    """Mock quality recommendations (WARNING severity)."""
    return [
        Recommendation(
            category="documentation",
            message="Complex role (47 tasks) lacks task descriptions",
            rationale="Large roles need documentation for maintainability",
            severity=Severity.WARNING,
            file_path="tasks/main.yml",
            line_number=None,
            remediation="Add # comments above tasks explaining their purpose",
            confidence=0.9,
            auto_fixable=False,
        ),
        Recommendation(
            category="documentation",
            message="15 variables used but not documented",
            rationale="Undocumented variables make roles hard to use",
            severity=Severity.WARNING,
            file_path="defaults/main.yml",
            line_number=None,
            remediation="Add comments describing each variable's purpose",
            confidence=0.85,
            auto_fixable=False,
        ),
    ]


@pytest.fixture
def enhancement_recommendations() -> list[Recommendation]:
    """Mock enhancement recommendations (INFO severity)."""
    return [
        Recommendation(
            category="best_practices",
            message="Consider adding examples/ directory",
            rationale="Example playbooks help users understand how to use the role",
            severity=Severity.INFO,
            file_path=None,
            line_number=None,
            remediation="Create examples/ with sample playbook.yml",
            confidence=0.6,
            auto_fixable=False,
        ),
        Recommendation(
            category="testing",
            message="Consider adding Molecule tests",
            rationale="Automated testing prevents regressions",
            severity=Severity.INFO,
            file_path=None,
            line_number=None,
            remediation="Run: molecule init scenario",
            confidence=0.7,
            auto_fixable=False,
        ),
    ]


@pytest.fixture
def all_recommendations(security_recommendations, quality_recommendations, enhancement_recommendations):
    """All recommendations combined (mixed severity)."""
    return security_recommendations + quality_recommendations + enhancement_recommendations


class TestRecommendationFormatter:
    """Test recommendation formatting."""

    def test_groups_by_severity(self, all_recommendations):
        """Test recommendations grouped by severity."""
        formatter = RecommendationFormatter()
        output = formatter.format_recommendations(all_recommendations)

        # Critical should come first, then warning, then info
        assert "🔴 CRITICAL" in output
        assert "🟡 WARNING" in output
        assert "💡 INFO" in output

        # Check ordering by finding section headers
        critical_pos = output.index("🔴 CRITICAL")
        warning_pos = output.index("🟡 WARNING")
        info_pos = output.index("💡 INFO")
        assert critical_pos < warning_pos < info_pos

    def test_hides_info_when_disabled(self, enhancement_recommendations):
        """Test INFO level hidden when show_info=False."""
        formatter = RecommendationFormatter()
        output = formatter.format_recommendations(
            enhancement_recommendations,
            show_info=False
        )

        assert "Consider adding examples/" not in output
        assert "hidden, use --show-info" in output

    def test_shows_location_when_available(self, security_recommendations):
        """Test file location displayed."""
        formatter = RecommendationFormatter()
        output = formatter.format_recommendations([security_recommendations[1]])

        assert "📍 tasks/main.yml:42" in output

    def test_shows_remediation_when_available(self, security_recommendations):
        """Test remediation steps displayed."""
        formatter = RecommendationFormatter()
        output = formatter.format_recommendations([security_recommendations[0]])

        assert "💡 Fix: Run: ansible-vault encrypt vault.yml" in output

    def test_empty_recommendations_shows_success_message(self):
        """Test empty list shows success message."""
        formatter = RecommendationFormatter()
        output = formatter.format_recommendations([])

        assert "✅" in output or "No recommendations" in output.lower()

    def test_formats_realistic_mixed_recommendations(self, all_recommendations):
        """Test formatting with realistic mixed severity recommendations."""
        formatter = RecommendationFormatter()
        output = formatter.format_recommendations(all_recommendations)

        # Check structure
        assert "📋 RECOMMENDATIONS" in output or "RECOMMENDATION" in output
        assert "🔴 CRITICAL" in output
        assert "🟡 WARNING" in output
        assert "💡 INFO" in output

        # Check ordering (critical before warning before info)
        critical_pos = output.index("🔴 CRITICAL")
        warning_pos = output.index("🟡 WARNING")
        info_pos = output.index("💡 INFO")
        assert critical_pos < warning_pos < info_pos

        # Check summary exists
        assert "3" in output  # 3 critical
        assert "2" in output  # 2 warnings or 2 suggestions

    def test_sorts_by_confidence_within_severity(self, security_recommendations):
        """Test recommendations sorted by confidence within same severity."""
        formatter = RecommendationFormatter()
        output = formatter.format_recommendations(security_recommendations)

        # Vault encryption (confidence=1.0) should come before debug exposure (confidence=0.8)
        vault_pos = output.index("Vault file not encrypted")
        debug_pos = output.index("sensitive variable exposed")
        assert vault_pos < debug_pos

    def test_formats_security_only(self, security_recommendations):
        """Test formatting with only security recommendations."""
        formatter = RecommendationFormatter()
        output = formatter.format_recommendations(security_recommendations)

        assert "🔴 CRITICAL" in output
        assert "🟡 WARNING" not in output
        assert "💡 INFO" not in output

    def test_shows_all_fields_when_present(self, security_recommendations):
        """Test all fields displayed when present."""
        formatter = RecommendationFormatter()
        output = formatter.format_recommendations([security_recommendations[0]])

        # Check message
        assert "Vault file not encrypted" in output

        # Check location
        assert "📍 vars/vault.yml:1" in output

        # Check remediation
        assert "💡 Fix: Run: ansible-vault encrypt vault.yml" in output

    def test_quality_recommendations_formatting(self, quality_recommendations):
        """Test formatting of quality/documentation recommendations."""
        formatter = RecommendationFormatter()
        output = formatter.format_recommendations(quality_recommendations)

        # Should have WARNING level
        assert "🟡 WARNING" in output

        # Check both quality messages are present
        assert "Complex role (47 tasks)" in output
        assert "15 variables used but not documented" in output

        # Check file paths are shown (even without line numbers)
        assert "tasks/main.yml" in output
        assert "defaults/main.yml" in output

    def test_enhancement_recommendations_formatting(self, enhancement_recommendations):
        """Test formatting of enhancement/best-practice recommendations."""
        formatter = RecommendationFormatter()
        output = formatter.format_recommendations(enhancement_recommendations)

        # Should have INFO level
        assert "💡 INFO" in output

        # Check both enhancement messages are present
        assert "Consider adding examples/" in output
        assert "Consider adding Molecule tests" in output

        # Check remediations are shown
        assert "Create examples/" in output
        assert "molecule init scenario" in output
