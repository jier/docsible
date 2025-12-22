"""Tests for extraction of enhanced integration details."""

from docsible.analyzers.complexity_analyzer import IntegrationType, detect_integrations


def test_api_endpoints_extracted():
    """Test API endpoint extraction through detect_integrations."""
    role_info = {
        "tasks": [
            {
                "file": "api.yml",
                "tasks": [
                    {
                        "name": "Call API",
                        "module": "uri",
                        "url": "https://api.example.com/v1/users",
                    },
                    {
                        "name": "Get data",
                        "module": "uri",
                        "url": "https://api.example.com/v1/posts",
                    },
                ],
            }
        ]
    }

    integrations = detect_integrations(role_info)

    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.API
    # Endpoints should be extracted
    assert len(integrations[0].endpoints) > 0
    assert any("api.example.com" in ep for ep in integrations[0].endpoints)


def test_network_ports_extracted():
    """Test network port extraction through detect_integrations."""
    role_info = {
        "tasks": [
            {
                "file": "firewall.yml",
                "tasks": [
                    {"name": "Open HTTPS", "module": "firewalld", "port": 443},
                    {"name": "Open HTTP", "module": "iptables", "port": "80"},
                ],
            }
        ]
    }

    integrations = detect_integrations(role_info)

    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.NETWORK
    # Ports should be extracted
    assert len(integrations[0].ports) > 0
    assert 443 in integrations[0].ports
    assert 80 in integrations[0].ports


def test_cloud_services_extracted():
    """Test cloud service extraction through detect_integrations."""
    role_info = {
        "tasks": [
            {
                "file": "cloud.yml",
                "tasks": [
                    {"name": "Create instance", "module": "amazon.aws.ec2"},
                    {"name": "Upload file", "module": "s3_bucket"},
                ],
            }
        ]
    }

    integrations = detect_integrations(role_info)

    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.CLOUD
    # Services should be extracted
    assert len(integrations[0].services) > 0
    assert "EC2" in integrations[0].services or "S3" in integrations[0].services
