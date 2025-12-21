"""Tests for ValueValidator (usefulness, actionable content)."""

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    ComplexityReport,
    IntegrationPoint,
    IntegrationType,
)
from docsible.validators.value import ValueValidator


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

        validator = ValueValidator()

        # With diagram
        issues_good, _ = validator.validate(doc_with_diagram,None, complexity_report)
        diagram_warnings = [i for i in issues_good if "diagram" in i.message.lower()]
        # Should have no warnings about missing diagrams
        assert len(diagram_warnings) == 0

        # Without diagram
        issues_bad, _ = validator.validate(
            doc_without_diagram,None, complexity_report
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

        validator = ValueValidator()

        # With security guidance
        issues_good, _ = validator.validate(doc_with_security,None, complexity_report)
        # Should not warn about security

        # Without security guidance
        issues_bad, metrics_bad = validator.validate(
            doc_without_security,None, complexity_report
        )
        # Should warn about missing security guidance
        assert any("security" in i.message.lower() for i in issues_bad)

    def test_brief_documentation_warning(self):
        """Test that very brief documentation gets a warning."""
        doc_brief = """# Role

Short.
"""
        validator = ValueValidator()
        issues, metrics = validator.validate(doc_brief,None, None)

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

        validator = ValueValidator()

        issues_good, metrics_good = validator.validate(doc_with_example,None, None)
        assert metrics_good["playbook_examples"] >= 1

        issues_bad, metrics_bad = validator.validate(doc_without_example, None, None)
        assert metrics_bad["playbook_examples"] == 0
        # Should have info about missing examples