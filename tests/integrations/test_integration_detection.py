"""Tests for detection of new integration types (CLOUD, NETWORK, CONTAINER, MONITORING)."""

from docsible.analyzers.complexity_analyzer import IntegrationType, detect_integrations


def test_cloud_aws_detection():
    """Test AWS cloud integration detection."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Create EC2 instance", "module": "amazon.aws.ec2"},
                    {"name": "Upload to S3", "module": "s3"},
                ],
            }
        ]
    }

    integrations = detect_integrations(role_info)

    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.CLOUD
    assert integrations[0].system_name == "AWS (Amazon Web Services)"
    assert integrations[0].task_count == 2
    assert "EC2" in integrations[0].services or "S3" in integrations[0].services


def test_cloud_azure_detection():
    """Test Azure cloud integration detection."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {
                        "name": "Create VM",
                        "module": "azure.azcollection.azure_rm_virtualmachine",
                    },
                ],
            }
        ]
    }

    integrations = detect_integrations(role_info)

    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.CLOUD
    assert "Azure" in integrations[0].system_name


def test_network_firewall_detection():
    """Test network/firewall integration detection."""
    role_info = {
        "tasks": [
            {
                "file": "firewall.yml",
                "tasks": [
                    {
                        "name": "Configure firewall",
                        "module": "firewalld",
                        "port": 443,
                    },
                    {
                        "name": "Set iptables rule",
                        "module": "iptables",
                        "port": "80",
                    },
                ],
            }
        ]
    }

    integrations = detect_integrations(role_info)

    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.NETWORK
    assert integrations[0].system_name == "Network Infrastructure"
    assert integrations[0].task_count == 2
    assert 80 in integrations[0].ports
    assert 443 in integrations[0].ports


def test_container_docker_detection():
    """Test Docker container integration detection."""
    role_info = {
        "tasks": [
            {
                "file": "container.yml",
                "tasks": [
                    {
                        "name": "Pull image",
                        "module": "community.docker.docker_image",
                    },
                    {"name": "Run container", "module": "docker_container"},
                ],
            }
        ]
    }

    integrations = detect_integrations(role_info)

    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.CONTAINER
    assert integrations[0].system_name == "Docker"
    assert "Docker" in integrations[0].services


def test_container_kubernetes_detection():
    """Test Kubernetes container integration detection."""
    role_info = {
        "tasks": [
            {
                "file": "k8s.yml",
                "tasks": [
                    {"name": "Deploy pod", "module": "community.kubernetes.k8s"},
                ],
            }
        ]
    }

    integrations = detect_integrations(role_info)

    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.CONTAINER
    assert integrations[0].system_name == "Kubernetes"


def test_monitoring_datadog_detection():
    """Test Datadog monitoring integration detection."""
    role_info = {
        "tasks": [
            {
                "file": "monitoring.yml",
                "tasks": [
                    {"name": "Install Datadog agent", "module": "datadog.agent"},
                ],
            }
        ]
    }

    integrations = detect_integrations(role_info)

    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.MONITORING
    assert integrations[0].system_name == "Datadog"


def test_monitoring_prometheus_detection():
    """Test Prometheus monitoring integration detection."""
    role_info = {
        "tasks": [
            {
                "file": "monitoring.yml",
                "tasks": [
                    {"name": "Configure Prometheus", "module": "prometheus.config"},
                ],
            }
        ]
    }

    integrations = detect_integrations(role_info)

    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.MONITORING
    assert "Prometheus" in integrations[0].system_name
