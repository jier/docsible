"""Tests for TruthValidator (accuracy verification)."""

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    ComplexityReport,
)
from docsible.validators.models import ValidationSeverity, ValidationType
from docsible.validators.truth import TruthValidator


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

        validator = TruthValidator()

        # Accurate count
        issues_good, metrics_good = validator.validate(
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
        issues_bad, metrics_bad = validator.validate(
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

        validator = TruthValidator()

        # Accurate category
        issues_good, _ = validator.validate(
            doc_accurate, None, complexity_report
        )
        complexity_errors = [
            i
            for i in issues_good
            if i.type == ValidationType.TRUTH and "complexity" in i.message.lower()
        ]
        assert len(complexity_errors) == 0

        # Inaccurate category
        issues_bad, _ = validator.validate(
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
        validator = TruthValidator()
        issues, metrics = validator.validate(doc, None, None)

        assert metrics["has_generated_markers"] is True
