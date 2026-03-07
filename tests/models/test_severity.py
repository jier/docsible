from docsible.models.severity import Severity


def test_severity_icons():
    """Test severity has correct emoji icons."""
    assert Severity.CRITICAL.icon == "🔴"
    assert Severity.WARNING.icon == "🟡"
    assert Severity.INFO.icon == "💡"

def test_severity_priority_ordering():
    """Test critical > warning > info."""
    assert Severity.CRITICAL.priority > Severity.WARNING.priority
    assert Severity.WARNING.priority > Severity.INFO.priority