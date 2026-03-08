
def test_public_api_imports():
    """Verify all public API items can be imported."""
    from docsible.validation import (
        DocumentationValidator,
        ValidationIssue,
        ValidationResult,
        ValidationSeverity,
        ValidationType,
        validate_documentation,
    )

    # All imports should succeed
    assert DocumentationValidator is not None
    assert validate_documentation is not None
    assert ValidationResult is not None
    assert ValidationIssue is not None
    assert ValidationSeverity is not None
    assert ValidationType is not None


def test_internal_not_exposed():
    """Verify internal implementation is not in public API."""
    from docsible import validation

    # These should NOT be in __all__
    assert "BaseValidator" not in validation.__all__
    assert "ClarityValidator" not in validation.__all__
    assert "calculate_score" not in validation.__all__


def test_direct_import_still_works():
    """Advanced users can still import directly if needed."""
    # This should work for power users
    from docsible.validation.base import BaseValidator
    from docsible.validation.clarity import ClarityValidator

    assert BaseValidator is not None
    assert ClarityValidator is not None
