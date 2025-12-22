"""Tests for complexity classification."""

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    classify_complexity,
)


def test_classify_simple_role():
    """Test classification of simple role (1-10 tasks)."""
    metrics = ComplexityMetrics(
        total_tasks=8,
        task_files=1,
        handlers=0,
        conditional_tasks=2,
        max_tasks_per_file=8,
        avg_tasks_per_file=8.0,
    )
    assert classify_complexity(metrics) == ComplexityCategory.SIMPLE


def test_classify_medium_role():
    """Test classification of medium role (11-25 tasks)."""
    metrics = ComplexityMetrics(
        total_tasks=18,
        task_files=2,
        handlers=1,
        conditional_tasks=5,
        max_tasks_per_file=12,
        avg_tasks_per_file=9.0,
    )
    assert classify_complexity(metrics) == ComplexityCategory.MEDIUM


def test_classify_complex_role():
    """Test classification of complex role (25+ tasks)."""
    metrics = ComplexityMetrics(
        total_tasks=30,
        task_files=4,
        handlers=3,
        conditional_tasks=15,
        max_tasks_per_file=15,
        avg_tasks_per_file=7.5,
    )
    assert classify_complexity(metrics) == ComplexityCategory.COMPLEX


def test_classify_boundary_conditions():
    """Test boundary conditions for complexity classification."""
    # Exactly 10 tasks = SIMPLE
    metrics_10 = ComplexityMetrics(
        total_tasks=10,
        task_files=1,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=10,
        avg_tasks_per_file=10.0,
    )
    assert classify_complexity(metrics_10) == ComplexityCategory.SIMPLE

    # Exactly 11 tasks = MEDIUM
    metrics_11 = ComplexityMetrics(
        total_tasks=11,
        task_files=1,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=11,
        avg_tasks_per_file=11.0,
    )
    assert classify_complexity(metrics_11) == ComplexityCategory.MEDIUM

    # Exactly 25 tasks = MEDIUM
    metrics_25 = ComplexityMetrics(
        total_tasks=25,
        task_files=2,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=15,
        avg_tasks_per_file=12.5,
    )
    assert classify_complexity(metrics_25) == ComplexityCategory.MEDIUM

    # Exactly 26 tasks = COMPLEX
    metrics_26 = ComplexityMetrics(
        total_tasks=26,
        task_files=2,
        handlers=0,
        conditional_tasks=0,
        max_tasks_per_file=16,
        avg_tasks_per_file=13.0,
    )
    assert classify_complexity(metrics_26) == ComplexityCategory.COMPLEX
