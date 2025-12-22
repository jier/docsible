"""Tests for ClarityValidator (readability, structure, formatting)."""

from docsible.validators.clarity import ClarityValidator
from docsible.validators.models import ValidationSeverity


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
        validator = ClarityValidator()
        issues, metrics = validator.validate(documentation=doc, role_info=None, complexity_report=None)

        # Should have minimal or no clarity issues
        error_issues = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert len(error_issues) == 0
        assert metrics["headings"] >= 5
        assert metrics["code_blocks"] >= 1

    def test_missing_headings_fails(self):
        """Test that documentation without headings fails clarity."""
        doc = "This is just plain text without any structure."

        validator = ClarityValidator()
        issues, metrics = validator.validate(documentation=doc, role_info=None, complexity_report=None)

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
        validator = ClarityValidator()
        issues, metrics = validator.validate(doc, role_info=None, complexity_report=None)

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
        validator = ClarityValidator()
        issues, metrics = validator.validate(documentation=doc, role_info=None, complexity_report=None)

        assert metrics["long_lines"] > 0
        # May generate info about long lines if >20% of lines are long