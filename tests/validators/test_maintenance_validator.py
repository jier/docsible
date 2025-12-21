"""Tests for MaintenanceValidator (completeness, coverage)."""

from typing import Any

from docsible.validators.maintenance import MaintenanceValidator


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

        validator = MaintenanceValidator()

        # With variables section
        issues_good, metrics_good = validator.validate(
            documentation=doc_with_vars, role_info=role_info, complexity_report=None
        )
        # Should have minimal warnings

        # Without variables section
        issues_bad, metrics_bad = validator.validate(
            documentation=doc_without_vars, role_info=role_info, complexity_report=None)
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
        validator = MaintenanceValidator()
        issues, metrics = validator.validate(documentation=doc, role_info=role_info, complexity_report=None )

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
        validator = MaintenanceValidator()
        issues, metrics = validator.validate(documentation=doc, role_info=role_info, complexity_report=None)

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
        validator = MaintenanceValidator()
        issues, metrics = validator.validate(documentation=doc, role_info=role_info, complexity_report=None)

        assert any("handler" in issue.message.lower() for issue in issues)
        assert metrics["handlers"] == 2
