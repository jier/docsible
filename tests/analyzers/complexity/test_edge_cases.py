"""Tests for edge cases and special scenarios."""

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    analyze_role_complexity,
)
from docsible.analyzers.patterns.detectors import ComplexityDetector


def test_empty_role():
    """Test analysis of role with no tasks."""
    role_info = {
        "name": "empty_role",
        "tasks": [],
        "handlers": [],
        "meta": {"dependencies": []},
    }

    report = analyze_role_complexity(role_info)
    assert report.category == ComplexityCategory.SIMPLE  # 0 tasks <= 10
    assert report.metrics.total_tasks == 0
    assert report.metrics.conditional_percentage == 0.0


def test_role_with_empty_task_files():
    """Test role with task files that have no tasks."""
    role_info = {
        "name": "test_role",
        "tasks": [
            {"file": "empty.yml", "tasks": []},
            {"file": "main.yml", "tasks": [{"name": "Task 1", "module": "debug"}]},
        ],
        "handlers": [],
        "meta": {"dependencies": []},
    }

    report = analyze_role_complexity(role_info)
    assert report.metrics.total_tasks == 1
    assert report.metrics.task_files == 2
    assert report.metrics.max_tasks_per_file == 1


def test_calculate_include_depth_simple():
    """Test depth calculation for simple linear chain."""
    detector = ComplexityDetector()

    include_graph = {
        "main.yml": ["setup.yml"],
        "setup.yml": ["install.yml"],
        "install.yml": [],
    }

    depth = detector._calculate_max_include_depth(include_graph, "main.yml", set())
    assert depth == 3


# FIXME Either change implementation and have depth == 1
# Assumption test Depth = 1, number of include layers before recursion becomes unsafe
# Assumption function Depth = 2, number of unique files reachable before hitting a cycle
def test_calculate_include_depth_with_cycle():
    """Test cycle detection."""
    detector = ComplexityDetector()

    include_graph = {"main.yml": ["setup.yml"], "setup.yml": ["main.yml"]}  # Cycle!

    depth = detector._calculate_max_include_depth(include_graph, "main.yml", set())
    assert depth == 2  # Should detect cycle and stop
