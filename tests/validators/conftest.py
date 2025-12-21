"""Shared fixtures for validator tests."""

import pytest

from docsible.analyzers.complexity_analyzer import (
    ComplexityCategory,
    ComplexityMetrics,
    ComplexityReport,
    IntegrationPoint,
    IntegrationType,
)


@pytest.fixture
def simple_role_info():
    """Fixture for a simple role structure."""
    return {
        "defaults": [{"file": "main.yml", "data": {"app_port": 8080}}],
        "vars": [],
        "handlers": [],
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Install app", "module": "apt"},
                ],
            }
        ],
        "dependencies": [],
    }


@pytest.fixture
def complex_role_info():
    """Fixture for a complex role structure."""
    return {
        "defaults": [
            {"file": "main.yml", "data": {"var1": "val1", "var2": "val2"}}
        ],
        "vars": [{"file": "main.yml", "data": {"var3": "val3"}}],
        "handlers": [
            {"name": "restart app", "module": "service"},
            {"name": "reload config", "module": "service"},
        ],
        "tasks": [
            {
                "file": "install.yml",
                "tasks": [
                    {"name": "Task 1", "module": "apt"},
                    {"name": "Task 2", "module": "copy"},
                ],
            },
            {
                "file": "configure.yml",
                "tasks": [
                    {"name": "Task 3", "module": "template"},
                    {"name": "Task 4", "module": "service"},
                ],
            },
        ],
        "dependencies": ["geerlingguy.apache"],
    }


@pytest.fixture
def simple_complexity_report():
    """Fixture for a SIMPLE complexity report."""
    return ComplexityReport(
        metrics=ComplexityMetrics(
            total_tasks=5,
            task_files=1,
            handlers=0,
            conditional_tasks=0,
            max_tasks_per_file=5,
            avg_tasks_per_file=5.0,
        ),
        category=ComplexityCategory.SIMPLE,
        integration_points=[],
        recommendations=[],
    )


@pytest.fixture
def complex_complexity_report():
    """Fixture for a COMPLEX complexity report with integrations."""
    return ComplexityReport(
        metrics=ComplexityMetrics(
            total_tasks=30,
            task_files=5,
            handlers=3,
            conditional_tasks=10,
            external_integrations=2,
            max_tasks_per_file=10,
            avg_tasks_per_file=6.0,
        ),
        category=ComplexityCategory.COMPLEX,
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


@pytest.fixture
def well_structured_doc():
    """Fixture for well-structured documentation."""
    return """# Test Role

## Description
This is a well-documented test role.

## Requirements
- Ansible 2.9+

## Role Variables
- `app_port`: Application port (default: 8080)

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


@pytest.fixture
def minimal_doc():
    """Fixture for minimal documentation."""
    return "# Title\n\nJust a brief description."
