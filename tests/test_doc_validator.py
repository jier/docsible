"""Tests for Priority 4: Documentation Validation Framework."""

from typing import Any

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    ComplexityReport,
    IntegrationPoint,
    IntegrationType,
)
from docsible.validators.doc_validator import (
    DocumentationValidator,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    ValidationType,
    validate_documentation,
)


class TestClarityValidation:
    """Test clarity validation (readability, structure, formatting)."""

    def test_well_structured_documentation_passes(self):
        """Test that well-structured documentation passes clarity checks."""
        doc = """# Test Role

## Description
This is a test role for validation.

## Requirements
- Ansible 2.9+

## Role Variables
Available variables:
- `test_var`: Description

## Dependencies
None

## Example Playbook
```yaml
- hosts: servers
  roles:
    - test_role
```

## License
MIT
"""
        validator = DocumentationValidator()
        issues, metrics = validator._validate_clarity(doc)

        # Should have minimal or no clarity issues
        error_issues = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(error_issues) == 0
        assert metrics["headings"] >= 5
        assert metrics["code_blocks"] >= 1

    def test_missing_headings_fails(self):
        """Test that documentation without headings fails clarity."""
        doc = "This is just plain text without any structure."

        validator = DocumentationValidator()
        issues, metrics = validator._validate_clarity(doc)

        # Should have error about missing headings
        assert any(
            issue.severity == ValidationSeverity.ERROR
            and "heading" in issue.message.lower()
            for issue in issues
        )
        assert metrics["headings"] == 0

    def test_unlabeled_code_blocks_warning(self):
        """Test that unlabeled code blocks generate warnings."""
        doc = """# Test Role

Some code without language label:
```
apt install foo
```
"""
        validator = DocumentationValidator()
        issues, metrics = validator._validate_clarity(doc)

        # Should warn about unlabeled code block
        assert any("unlabeled" in issue.message.lower() for issue in issues)

    def test_long_lines_info(self):
        """Test that excessive long lines generate info messages."""
        long_line = "x" * 150
        doc = f"""# Test Role

{long_line}
{long_line}
{long_line}
{long_line}
{long_line}
"""
        validator = DocumentationValidator()
        issues, metrics = validator._validate_clarity(doc)

        assert metrics["long_lines"] > 0
        # May generate info about long lines if >20% of lines are long


class TestMaintenanceValidation:
    """Test maintenance validation (completeness, coverage)."""

    def test_documents_all_variables(self):
        """Test validation of variable documentation."""
        role_info = {
            "defaults": [
                {"file": "main.yml", "data": {"var1": "value1", "var2": "value2"}}
            ],
            "vars": [],
            "handlers": [],
            "tasks": [],
            "dependencies": [],
        }

        doc_with_vars = """# Test Role

## Role Variables
- `var1`: First variable
- `var2`: Second variable
"""

        doc_without_vars = """# Test Role

No variables section here.
"""

        validator = DocumentationValidator()

        # With variables section
        issues_good, metrics_good = validator._validate_maintenance(
            doc_with_vars, role_info
        )
        # Should have minimal warnings

        # Without variables section
        issues_bad, metrics_bad = validator._validate_maintenance(
            doc_without_vars, role_info
        )
        # Should warn about missing variables section
        assert any("variables" in issue.message.lower() for issue in issues_bad)
        assert metrics_bad["total_variables"] == 2

    def test_missing_example_playbook_warning(self):
        """Test that missing examples generate warnings."""
        role_info: dict[str, Any] | None = {
            "defaults": [],
            "vars": [],
            "handlers": [],
            "tasks": [],
            "dependencies": [],
        }
        doc = """# Test Role

Just description, no examples.
"""
        validator = DocumentationValidator()
        issues, metrics = validator._validate_maintenance(doc, role_info)

        assert any("example" in issue.message.lower() for issue in issues)
        assert not metrics["has_example"]

    def test_undocumented_dependencies_warning(self):
        """Test warning for undocumented dependencies."""
        role_info = {
            "defaults": [],
            "vars": [],
            "handlers": [],
            "tasks": [],
            "dependencies": ["geerlingguy.apache", "geerlingguy.mysql"],
        }

        doc = """# Test Role

Just a basic description without any mention of other roles.
"""
        validator = DocumentationValidator()
        issues, metrics = validator._validate_maintenance(doc, role_info)

        assert any("dependencies" in issue.message.lower() for issue in issues)
        assert metrics["dependencies"] == 2

    def test_undocumented_handlers_info(self):
        """Test info message for undocumented handlers."""
        role_info = {
            "defaults": [],
            "vars": [],
            "handlers": [
                {"name": "restart apache", "module": "service"},
                {"name": "reload nginx", "module": "service"},
            ],
            "tasks": [],
            "dependencies": [],
        }

        doc = """# Test Role

Basic description without mentioning event triggers.
"""
        validator = DocumentationValidator()
        issues, metrics = validator._validate_maintenance(doc, role_info)

        assert any("handler" in issue.message.lower() for issue in issues)
        assert metrics["handlers"] == 2


class TestTruthValidation:
    """Test truth validation (accuracy verification)."""

    def test_accurate_task_count(self):
        """Test validation of task count accuracy."""
        role_info = {
            "tasks": [
                {
                    "file": "main.yml",
                    "tasks": [
                        {"name": "Task 1", "module": "apt"},
                        {"name": "Task 2", "module": "service"},
                        {"name": "Task 3", "module": "copy"},
                    ],
                }
            ]
        }

        doc_accurate = """# Test Role

This role contains **3 tasks** across all task files.
"""

        doc_inaccurate = """# Test Role

This role contains **10 tasks** across all task files.
"""

        validator = DocumentationValidator()

        # Accurate count
        issues_good, metrics_good = validator._validate_truth(
            doc_accurate, role_info, None
        )
        assert metrics_good["actual_tasks"] == 3
        # Should not have task count error
        task_count_errors = [
            i
            for i in issues_good
            if i.type == ValidationType.TRUTH and "task" in i.message.lower()
        ]
        assert len(task_count_errors) == 0

        # Inaccurate count
        issues_bad, metrics_bad = validator._validate_truth(
            doc_inaccurate, role_info, None
        )
        # Should have error about incorrect task count
        assert any(
            i.severity == ValidationSeverity.ERROR and "10 tasks" in i.message
            for i in issues_bad
        )

    def test_accurate_complexity_category(self):
        """Test validation of complexity category claims."""
        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=30,
                task_files=5,
                handlers=2,
                conditional_tasks=10,
                max_tasks_per_file=10,
                avg_tasks_per_file=6.0,
            ),
            category=ComplexityCategory.COMPLEX,
            integration_points=[],
            recommendations=[],
        )

        doc_accurate = """# Test Role

This is a **COMPLEX role** with 30 tasks.
"""

        doc_inaccurate = """# Test Role

This is a **SIMPLE role** with just a few tasks.
"""

        validator = DocumentationValidator()

        # Accurate category
        issues_good, _ = validator._validate_truth(
            doc_accurate, None, complexity_report
        )
        complexity_errors = [
            i
            for i in issues_good
            if i.type == ValidationType.TRUTH and "complexity" in i.message.lower()
        ]
        assert len(complexity_errors) == 0

        # Inaccurate category
        issues_bad, _ = validator._validate_truth(
            doc_inaccurate, None, complexity_report
        )
        assert any(
            i.severity == ValidationSeverity.ERROR and "SIMPLE" in i.message
            for i in issues_bad
        )

    def test_generated_markers_tracked(self):
        """Test that auto-generated markers are tracked."""
        doc = """# Test Role
<!-- DOCSIBLE GENERATED -->

Content here.
"""
        validator = DocumentationValidator()
        issues, metrics = validator._validate_truth(doc, None, None)

        assert metrics["has_generated_markers"] is True


class TestValueValidation:
    """Test value validation (usefulness, actionable content)."""

    def test_complex_role_needs_diagrams(self):
        """Test that complex roles should have diagrams."""
        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=30,
                task_files=5,
                handlers=2,
                conditional_tasks=10,
                max_tasks_per_file=10,
                avg_tasks_per_file=6.0,
            ),
            category=ComplexityCategory.COMPLEX,
            integration_points=[],
            recommendations=[],
        )

        doc_with_diagram = """# Test Role

```mermaid
graph TB
    A --> B
```
"""

        doc_without_diagram = """# Test Role

No diagrams here.
"""

        validator = DocumentationValidator()

        # With diagram
        issues_good, _ = validator._validate_value(doc_with_diagram, complexity_report)
        diagram_warnings = [i for i in issues_good if "diagram" in i.message.lower()]
        # Should have no warnings about missing diagrams
        assert len(diagram_warnings) == 0

        # Without diagram
        issues_bad, _ = validator._validate_value(
            doc_without_diagram, complexity_report
        )
        # Should warn about missing diagrams
        assert any("diagram" in i.message.lower() for i in issues_bad)

    def test_integrations_need_security_guidance(self):
        """Test that roles with integrations need security guidance."""
        complexity_report = ComplexityReport(
            metrics=ComplexityMetrics(
                total_tasks=15,
                task_files=2,
                handlers=1,
                conditional_tasks=5,
                external_integrations=2,
                max_tasks_per_file=10,
                avg_tasks_per_file=7.5,
            ),
            category=ComplexityCategory.MEDIUM,
            integration_points=[
                IntegrationPoint(
                    type=IntegrationType.DATABASE,
                    system_name="PostgreSQL",
                    modules_used=["postgresql_db"],
                    task_count=3,
                    uses_credentials=True,
                )
            ],
            recommendations=[],
        )

        doc_with_security = """# Test Role

## Security Considerations
Credentials are required for database access.
"""

        doc_without_security = """# Test Role

Just a basic description.
"""

        validator = DocumentationValidator()

        # With security guidance
        issues_good, _ = validator._validate_value(doc_with_security, complexity_report)
        # Should not warn about security

        # Without security guidance
        issues_bad, metrics_bad = validator._validate_value(
            doc_without_security, complexity_report
        )
        # Should warn about missing security guidance
        assert any("security" in i.message.lower() for i in issues_bad)

    def test_brief_documentation_warning(self):
        """Test that very brief documentation gets a warning."""
        doc_brief = """# Role

Short.
"""
        validator = DocumentationValidator()
        issues, metrics = validator._validate_value(doc_brief, None)

        assert metrics["word_count"] < 200
        assert any("brief" in i.message.lower() for i in issues)

    def test_actionable_examples_valued(self):
        """Test that playbook examples are valued."""
        doc_with_example = """# Test Role

## Example Playbook
```yaml
- hosts: servers
  roles:
    - role: test_role
```
"""

        doc_without_example = """# Test Role

Description only.
"""

        validator = DocumentationValidator()

        issues_good, metrics_good = validator._validate_value(doc_with_example, None)
        assert metrics_good["playbook_examples"] >= 1

        issues_bad, metrics_bad = validator._validate_value(doc_without_example, None)
        assert metrics_bad["playbook_examples"] == 0
        # Should have info about missing examples


class TestFullValidation:
    """Test complete validation workflow."""

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

    def test_score_calculation(self):
        """Test quality score calculation."""
        validator = DocumentationValidator()

        # Test with different issue severities
        issues_severe = [
            ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.ERROR,
                message="Error 1",
            ),
            ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.ERROR,
                message="Error 2",
            ),
        ]

        score_severe = validator._calculate_score(issues_severe, {})
        # 100 - (2 * 15) = 70
        assert score_severe == 70.0

        issues_mixed = [
            ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.ERROR,
                message="Error",
            ),
            ValidationIssue(
                type=ValidationType.MAINTENANCE,
                severity=ValidationSeverity.WARNING,
                message="Warning",
            ),
            ValidationIssue(
                type=ValidationType.VALUE,
                severity=ValidationSeverity.INFO,
                message="Info",
            ),
        ]

        score_mixed = validator._calculate_score(issues_mixed, {})
        # 100 - 15 - 5 - 2 = 78
        assert score_mixed == 78.0

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
