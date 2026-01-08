"""Tests for Priority 3: Enhanced Integration Features."""

from docsible.analyzers.complexity_analyzer import (
    IntegrationPoint,
    IntegrationType,
    detect_integrations,
)
from docsible.utils.integration_diagram import generate_integration_boundary
from docsible.utils.network_topology import (
    format_integration_details,
    generate_network_topology,
    should_generate_network_topology,
)


class TestNewIntegrationTypes:
    """Test detection of new integration types (CLOUD, NETWORK, CONTAINER, MONITORING)."""

    def test_cloud_aws_detection(self):
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

    def test_cloud_azure_detection(self):
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

    def test_network_firewall_detection(self):
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

    def test_container_docker_detection(self):
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

    def test_container_kubernetes_detection(self):
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

    def test_monitoring_datadog_detection(self):
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

    def test_monitoring_prometheus_detection(self):
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


class TestEnhancedDetails:
    """Test extraction of enhanced integration details through public API."""

    def test_api_endpoints_extracted(self):
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

    def test_network_ports_extracted(self):
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

    def test_cloud_services_extracted(self):
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


class TestEnhancedDiagrams:
    """Test enhanced diagram generation for new integration types."""

    def test_diagram_with_cloud_integration(self):
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

    def test_diagram_with_network_integration(self):
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

    def test_diagram_with_container_integration(self):
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

    def test_diagram_with_monitoring_integration(self):
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

    def test_diagram_with_mixed_integrations(self):
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


class TestNetworkTopology:
    """Test network topology diagram generation."""

    def test_generate_network_topology(self):
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

    def test_network_topology_with_no_network_integrations(self):
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

    def test_should_generate_network_topology(self):
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

    def test_format_integration_details_api(self):
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

    def test_format_integration_details_network(self):
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

    def test_format_integration_details_cloud(self):
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
