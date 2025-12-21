"""Shared fixtures for integration tests."""

import pytest

from docsible.analyzers.complexity_analyzer import IntegrationPoint, IntegrationType


@pytest.fixture
def api_integration():
    """Sample API integration point."""
    return IntegrationPoint(
        type=IntegrationType.API,
        system_name="REST APIs",
        modules_used=["uri", "get_url"],
        task_count=2,
        uses_credentials=True,
        endpoints=["https://api.example.com/v1/users"],
    )


@pytest.fixture
def database_integration():
    """Sample database integration point."""
    return IntegrationPoint(
        type=IntegrationType.DATABASE,
        system_name="PostgreSQL",
        modules_used=["postgresql_db", "postgresql_user"],
        task_count=3,
        uses_credentials=True,
    )


@pytest.fixture
def cloud_integration():
    """Sample cloud integration point."""
    return IntegrationPoint(
        type=IntegrationType.CLOUD,
        system_name="AWS (Amazon Web Services)",
        modules_used=["amazon.aws.ec2", "s3"],
        task_count=5,
        uses_credentials=True,
        services=["EC2", "S3"],
    )


@pytest.fixture
def network_integration():
    """Sample network integration point."""
    return IntegrationPoint(
        type=IntegrationType.NETWORK,
        system_name="Network Infrastructure",
        modules_used=["firewalld", "iptables"],
        task_count=3,
        uses_credentials=False,
        ports=[80, 443, 8080],
    )


@pytest.fixture
def container_integration():
    """Sample container integration point."""
    return IntegrationPoint(
        type=IntegrationType.CONTAINER,
        system_name="Docker",
        modules_used=["community.docker.docker_container"],
        task_count=2,
        uses_credentials=False,
        services=["Docker"],
    )


@pytest.fixture
def monitoring_integration():
    """Sample monitoring integration point."""
    return IntegrationPoint(
        type=IntegrationType.MONITORING,
        system_name="Datadog",
        modules_used=["datadog.agent"],
        task_count=1,
        uses_credentials=True,
        services=["Datadog"],
    )
