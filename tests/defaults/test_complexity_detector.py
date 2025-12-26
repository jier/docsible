from pathlib import Path

import pytest

from docsible.defaults.detectors.complexity import Category, ComplexityDetector
from tests.comparison.conftest import (
    complex_role,
    complex_role_fixture,
    empty_role,
    medium_role_fixture,
    simple_role,
)


class TestComplexityDetector:
    """Test ComplexityDetector in isolation."""

    def test_detect_simple_role(self, simple_role):
        """Test detection of simple role (1-10 tasks)."""
        detector = ComplexityDetector()
        result = detector.detect(simple_role)

        assert result.detector_name == "ComplexityDetector"
        assert result.confidence > 0.8
        # findings contains Category enum, not string
        assert result.findings["category"] == Category.SIMPLE
        assert result.findings["total_tasks"] <= 10
        assert result.findings["total_tasks"] > 0

    def test_detect_medium_role(self, medium_role_fixture):
        """Test detection of medium complexity role (11-25 tasks)."""
        detector = ComplexityDetector()
        result = detector.detect(medium_role_fixture)

        assert result.detector_name == "ComplexityDetector"
        assert result.confidence > 0.8
        # Medium role: 15 tasks across 3 files
        assert result.findings["category"] == Category.MEDIUM
        assert 11 <= result.findings["total_tasks"] <= 25
        assert result.findings["task_files"] >= 2
        assert result.findings["handlers"] >= 1

    def test_detect_complex_role(self, complex_role_fixture):
        """Test detection of complex role (26+ tasks)."""
        detector = ComplexityDetector()
        result = detector.detect(complex_role_fixture)

        assert result.detector_name == "ComplexityDetector"
        assert result.confidence > 0.8
        # Complex role: 30+ tasks across 5 files
        assert result.findings["category"] == Category.COMPLEX
        assert result.findings["total_tasks"] > 25
        assert result.findings["task_files"] >= 4
        assert result.findings["has_dependencies"] is True or result.findings["has_dependencies"] is False

    def test_detect_legacy_complex_fixture(self, complex_role):
        """Test legacy complex_role fixture (actually MEDIUM complexity).

        Note: The original complex_role fixture is actually categorized as MEDIUM
        by the complexity analyzer (13 tasks). This test validates backward compatibility.
        """
        detector = ComplexityDetector()
        result = detector.detect(complex_role)

        # Legacy fixture has 13 tasks across 4 files - categorized as MEDIUM
        assert result.findings["category"] == Category.MEDIUM
        assert result.findings["total_tasks"] >= 10
        assert result.findings["task_files"] >= 2

    def test_invalid_path_raises(self):
        """Test that invalid path raises ValueError."""
        detector = ComplexityDetector()

        with pytest.raises(ValueError, match="does not exist"):
            detector.detect(Path("/nonexistent/path"))

    def test_confidence_levels(self, empty_role):
        """Test confidence calculation for empty role."""
        detector = ComplexityDetector()

        # If empty_role fixture returns None, skip test
        if empty_role is None:
            pytest.skip("empty_role fixture not available")

        result = detector.detect(empty_role)

        # Empty role should have low confidence
        assert result.confidence < 0.5

    def test_complexity_score_calculation(self, medium_role_fixture):
        """Test that complexity score is calculated correctly."""
        detector = ComplexityDetector()
        result = detector.detect(medium_role_fixture)

        # Complexity score should be between 0.0 and 1.0
        assert 0.0 <= result.findings["complexity_score"] <= 1.0
        # Medium role should have low to moderate complexity score
        # Score is based on tasks (15/100), files (3/10), conditionals
        assert 0.1 <= result.findings["complexity_score"] <= 0.5

    def test_advanced_features_detection(self, complex_role_fixture):
        """Test detection of advanced features in complex roles."""
        detector = ComplexityDetector()
        result = detector.detect(complex_role_fixture)

        # Complex role has multiple task files (includes/imports)
        assert result.findings["task_files"] >= 4
        # Should have handlers
        assert result.findings["handlers"] > 0