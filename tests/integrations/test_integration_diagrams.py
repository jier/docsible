"""Tests for enhanced diagram generation for new integration types."""

from docsible.analyzers.complexity_analyzer import IntegrationPoint, IntegrationType
from docsible.utils.integration_diagram import generate_integration_boundary


def test_diagram_with_cloud_integration():
    """Test diagram generation with cloud integration."""
    integrations = [
        IntegrationPoint(
            type=IntegrationType.CLOUD,
            system_name="AWS (Amazon Web Services)",
            modules_used=["amazon.aws.ec2", "s3"],
            task_count=5,
            uses_credentials=True,
            services=["EC2", "S3"],
        )
    ]

    diagram = generate_integration_boundary(integrations)

    assert diagram is not None
    assert "AWS (Amazon Web Services)" in diagram
    assert "cloudStyle" in diagram
    assert "credentials" in diagram


def test_diagram_with_network_integration():
    """Test diagram generation with network integration."""
    integrations = [
        IntegrationPoint(
            type=IntegrationType.NETWORK,
            system_name="Network Infrastructure",
            modules_used=["firewalld", "iptables"],
            task_count=3,
            uses_credentials=False,
            ports=[80, 443, 8080],
        )
    ]

    diagram = generate_integration_boundary(integrations)

    assert diagram is not None
    assert "Network Infrastructure" in diagram
    assert "networkStyle" in diagram


def test_diagram_with_container_integration():
    """Test diagram generation with container integration."""
    integrations = [
        IntegrationPoint(
            type=IntegrationType.CONTAINER,
            system_name="Docker",
            modules_used=["community.docker.docker_container"],
            task_count=2,
            uses_credentials=False,
            services=["Docker"],
        )
    ]

    diagram = generate_integration_boundary(integrations)

    assert diagram is not None
    assert "Docker" in diagram
    assert "containerStyle" in diagram


def test_diagram_with_monitoring_integration():
    """Test diagram generation with monitoring integration."""
    integrations = [
        IntegrationPoint(
            type=IntegrationType.MONITORING,
            system_name="Datadog",
            modules_used=["datadog.agent"],
            task_count=1,
            uses_credentials=True,
            services=["Datadog"],
        )
    ]

    diagram = generate_integration_boundary(integrations)

    assert diagram is not None
    assert "Datadog" in diagram
    assert "monitoringStyle" in diagram


def test_diagram_with_mixed_integrations():
    """Test diagram with multiple types of integrations."""
    integrations = [
        IntegrationPoint(
            type=IntegrationType.CLOUD,
            system_name="AWS (Amazon Web Services)",
            modules_used=["ec2"],
            task_count=2,
            uses_credentials=True,
            services=["EC2"],
        ),
        IntegrationPoint(
            type=IntegrationType.CONTAINER,
            system_name="Docker",
            modules_used=["docker_container"],
            task_count=1,
            uses_credentials=False,
            services=["Docker"],
        ),
        IntegrationPoint(
            type=IntegrationType.MONITORING,
            system_name="Prometheus",
            modules_used=["prometheus.config"],
            task_count=1,
            uses_credentials=False,
            services=["Prometheus"],
        ),
    ]

    diagram = generate_integration_boundary(integrations)

    assert diagram is not None
    assert "cloudStyle" in diagram
    assert "containerStyle" in diagram
    assert "monitoringStyle" in diagram
    assert diagram.count("credentials") == 1  # Only AWS uses credentials
