"""Tests for recommendation generation."""

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    IntegrationPoint,
    IntegrationType,
    generate_recommendations,
)


def test_recommendations_for_complex_role():
    """Test recommendations for complex role."""
    metrics = ComplexityMetrics(
        total_tasks=35,
        task_files=3,
        handlers=2,
        conditional_tasks=15,
        max_tasks_per_file=20,
        avg_tasks_per_file=11.7,
    )

    recommendations = generate_recommendations(
        metrics,
        ComplexityCategory.COMPLEX,
        [],
        file_details=[],
        hotspots=[],
        inflection_points=[],
        role_info={"tasks": []},
    )

    assert len(recommendations) >= 2
    assert any("complex" in rec.lower() for rec in recommendations)
    assert any("20 tasks" in rec for rec in recommendations)


def test_recommendations_for_high_composition():
    """Test recommendations for high composition complexity."""
    metrics = ComplexityMetrics(
        total_tasks=15,
        task_files=2,
        handlers=1,
        conditional_tasks=3,
        role_dependencies=5,
        role_includes=2,
        task_includes=1,
        max_tasks_per_file=8,
        avg_tasks_per_file=7.5,
    )

    recommendations = generate_recommendations(
        metrics,
        ComplexityCategory.MEDIUM,
        [],
        file_details=[],
        hotspots=[],
        inflection_points=[],
        role_info={"tasks": []},
    )

    # Composition score = (5*2) + 2 + 1 = 13 (>= 8, so should recommend documenting dependencies)
    assert any("composition" in rec.lower() for rec in recommendations)
    assert any("dependencies" in rec.lower() for rec in recommendations)


def test_recommendations_for_multiple_integrations():
    """Test recommendations for multiple external integrations."""
    metrics = ComplexityMetrics(
        total_tasks=20,
        task_files=2,
        handlers=1,
        conditional_tasks=5,
        external_integrations=4,
        max_tasks_per_file=12,
        avg_tasks_per_file=10.0,
    )

    integration_points = [
        IntegrationPoint(
            type=IntegrationType.API,
            system_name="REST API",
            modules_used=["uri"],
            task_count=2,
            uses_credentials=True,
        ),
        IntegrationPoint(
            type=IntegrationType.DATABASE,
            system_name="PostgreSQL",
            modules_used=["postgresql_db"],
            task_count=3,
            uses_credentials=True,
        ),
        IntegrationPoint(
            type=IntegrationType.VAULT,
            system_name="Vault",
            modules_used=["hashi_vault"],
            task_count=1,
            uses_credentials=True,
        ),
        IntegrationPoint(
            type=IntegrationType.API,
            system_name="GraphQL API",
            modules_used=["uri"],
            task_count=1,
            uses_credentials=False,
        ),
    ]

    recommendations = generate_recommendations(
        metrics,
        ComplexityCategory.MEDIUM,
        integration_points,
        file_details=[],
        hotspots=[],
        inflection_points=[],
        role_info={"tasks": []},
    )

    # Should recommend architecture diagram for multiple integrations
    assert any("integration" in rec.lower() for rec in recommendations)
    assert any("architecture diagram" in rec.lower() for rec in recommendations)


def test_recommendations_for_credentials():
    """Test recommendations when external systems require credentials."""
    metrics = ComplexityMetrics(
        total_tasks=12,
        task_files=2,
        handlers=0,
        conditional_tasks=2,
        external_integrations=1,
        max_tasks_per_file=6,
        avg_tasks_per_file=6.0,
    )

    integration_points = [
        IntegrationPoint(
            type=IntegrationType.DATABASE,
            system_name="PostgreSQL",
            modules_used=["postgresql_db"],
            task_count=3,
            uses_credentials=True,
        )
    ]

    recommendations = generate_recommendations(
        metrics,
        ComplexityCategory.MEDIUM,
        integration_points,
        file_details=[],
        hotspots=[],
        inflection_points=[],
        role_info={"tasks": []},
    )

    assert any(
        "credentials" in rec.lower() or "authentication" in rec.lower()
        for rec in recommendations
    )


def test_recommendations_for_simple_role():
    """Test recommendations for manageable simple role."""
    metrics = ComplexityMetrics(
        total_tasks=8,
        task_files=1,
        handlers=1,
        conditional_tasks=2,
        max_tasks_per_file=8,
        avg_tasks_per_file=8.0,
    )

    recommendations = generate_recommendations(
        metrics,
        ComplexityCategory.SIMPLE,
        [],
        file_details=[],
        hotspots=[],
        inflection_points=[],
        role_info={"tasks": []},
    )

    # Should indicate role is manageable
    assert any(
        "manageable" in rec.lower() or "standard" in rec.lower()
        for rec in recommendations
    )
