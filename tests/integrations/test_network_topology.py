"""Tests for network topology diagram generation."""

from docsible.analyzers.complexity_analyzer import IntegrationPoint, IntegrationType
from docsible.utils.network_topology import (
    format_integration_details,
    generate_network_topology,
    should_generate_network_topology,
)


def test_generate_network_topology():
    """Test basic network topology generation."""
    integrations = [
        IntegrationPoint(
            type=IntegrationType.NETWORK,
            system_name="Firewall",
            modules_used=["firewalld", "iptables"],
            task_count=3,
            uses_credentials=False,
            ports=[80, 443, 8080],
        )
    ]

    diagram = generate_network_topology(integrations)

    assert diagram is not None
    assert "graph TB" in diagram
    assert "Network Infrastructure" in diagram
    assert "Firewall" in diagram
    assert "80" in diagram or "443" in diagram


def test_network_topology_with_no_network_integrations():
    """Test that no diagram is generated without network integrations."""
    integrations = [
        IntegrationPoint(
            type=IntegrationType.API,
            system_name="REST API",
            modules_used=["uri"],
            task_count=1,
            uses_credentials=False,
        )
    ]

    diagram = generate_network_topology(integrations)

    assert diagram is None


def test_should_generate_network_topology():
    """Test decision logic for network topology generation."""
    # With network integration
    integrations = [
        IntegrationPoint(
            type=IntegrationType.NETWORK,
            system_name="Firewall",
            modules_used=["firewalld"],
            task_count=1,
            uses_credentials=False,
            ports=[443],
        )
    ]
    assert should_generate_network_topology(integrations) is True

    # Without network integration
    integrations = [
        IntegrationPoint(
            type=IntegrationType.API,
            system_name="API",
            modules_used=["uri"],
            task_count=1,
            uses_credentials=False,
        )
    ]
    assert should_generate_network_topology(integrations) is False


def test_format_integration_details_api():
    """Test formatting API integration details."""
    integration = IntegrationPoint(
        type=IntegrationType.API,
        system_name="REST APIs",
        modules_used=["uri"],
        task_count=1,
        uses_credentials=False,
        endpoints=["https://api.example.com/v1", "https://api.other.com/data"],
    )

    details = format_integration_details(integration)

    assert "endpoints" in details
    assert len(details["endpoints"]) == 2


def test_format_integration_details_network():
    """Test formatting network integration details."""
    integration = IntegrationPoint(
        type=IntegrationType.NETWORK,
        system_name="Firewall",
        modules_used=["firewalld"],
        task_count=1,
        uses_credentials=False,
        ports=[80, 443, 8080],
    )

    details = format_integration_details(integration)

    assert "ports" in details
    assert "80" in details["ports"]
    assert "443" in details["ports"]


def test_format_integration_details_cloud():
    """Test formatting cloud integration details."""
    integration = IntegrationPoint(
        type=IntegrationType.CLOUD,
        system_name="AWS",
        modules_used=["ec2", "s3"],
        task_count=2,
        uses_credentials=True,
        services=["EC2", "S3"],
    )

    details = format_integration_details(integration)

    assert "services" in details
    assert "EC2" in details["services"]
    assert "S3" in details["services"]
