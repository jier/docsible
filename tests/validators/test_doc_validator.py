"""Integration tests for DocumentationValidator orchestrator."""

from typing import Any

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    ComplexityReport,
)
from docsible.validators.doc_validator import (
    DocumentationValidator,
    validate_documentation,
)
from docsible.validators.models import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    ValidationType,
)


class TestDocumentationValidator:
    """Integration tests for complete validation workflow."""

    def test_high_quality_documentation_passes(self):
        """Test that high-quality documentation passes all checks."""
        role_info = {
            "defaults": [{"file": "main.yml", "data": {"apache_port": 80}}],
            "vars": [],
            "handlers": [{"name": "restart apache", "module": "service"}],
            "tasks": [
                {
                    "file": "main.yml",
                    "tasks": [
                        {"name": "Install Apache", "module": "apt"},
                        {"name": "Start Apache", "module": "service"},
                    ],
                }
            ],
            "dependencies": [],
        }

        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=2,
                task_files=1,
                handlers=1,
                conditional_tasks=0,
                max_tasks_per_file=2,
                avg_tasks_per_file=2.0,
            ),
            category=ComplexityCategory.SIMPLE,
            integration_points=[],
            recommendations=[],
        )

        doc = """# Apache Role

## Description
Installs and configures Apache web server.

## Requirements
- Ansible 2.9+
- Debian/Ubuntu

## Role Variables
- `apache_port`: Port for Apache to listen on (default: 80)

## Dependencies
None

## Example Playbook
```yaml
- hosts: webservers
  roles:
    - role: apache
      apache_port: 8080
```

## Handlers
- `restart apache`: Restarts the Apache service

## License
MIT

## Author
Test Author
"""

        result = validate_documentation(
            doc, role_info, complexity_report, min_score=70.0
        )

        assert result.score >= 70.0
        assert result.passed is True
        # May have some INFO suggestions but should pass

    def test_poor_documentation_fails(self):
        """Test that poor quality documentation fails validation."""
        role_info = {
            "defaults": [{"file": "main.yml", "data": {"var1": "val", "var2": "val"}}],
            "vars": [],
            "handlers": [],
            "tasks": [
                {"file": "main.yml", "tasks": [{"name": "Task 1", "module": "apt"}]}
            ],
            "dependencies": ["some.role"],
        }

        doc_poor = "Just a title"

        result = validate_documentation(doc_poor, role_info, None, min_score=70.0)

        assert result.score < 70.0
        assert result.passed is False
        assert len(result.issues) > 0
        # Should have errors about missing structure

    def test_validator_with_custom_min_score(self):
        """Test validator with custom minimum score."""
        validator = DocumentationValidator(min_score=90.0)
        assert validator.min_score == 90.0

        # Even a small issue might cause failure with high min_score
        doc = "# Title\n\nSome content but no examples."
        role_info: dict[str, Any] | None = {
            "defaults": [],
            "vars": [],
            "handlers": [],
            "tasks": [],
            "dependencies": [],
        }

        result = validator.validate(doc, role_info, None)
        # May not pass the 90.0 threshold
        if result.score < 90.0:
            assert result.passed is False


class TestValidationResult:
    """Test ValidationResult helper methods."""

    def test_validation_result_filtering(self):
        """Test ValidationResult filtering methods."""
        result = ValidationResult(
            passed=False,
            score=60.0,
            issues=[
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.ERROR,
                    message="Test error",
                ),
                ValidationIssue(
                    type=ValidationType.MAINTENANCE,
                    severity=ValidationSeverity.WARNING,
                    message="Test warning",
                ),
                ValidationIssue(
                    type=ValidationType.VALUE,
                    severity=ValidationSeverity.INFO,
                    message="Test info",
                ),
            ],
        )

        # Test filtering by type
        clarity_issues = result.get_issues_by_type(ValidationType.CLARITY)
        assert len(clarity_issues) == 1
        assert clarity_issues[0].message == "Test error"

        # Test filtering by severity
        errors = result.get_issues_by_severity(ValidationSeverity.ERROR)
        assert len(errors) == 1

        # Test has_errors
        assert result.has_errors() is True