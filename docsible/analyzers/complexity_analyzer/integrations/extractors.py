"""Utility functions for extracting integration details."""

from typing import Any


class EndpointExtractor:
    """Extract API endpoints from tasks."""

    @staticmethod
    def extract(tasks: list[dict[str, Any]]) -> list[str]:
        """Extract endpoint URLs from uri/http module tasks.

        Args:
            tasks: List of task dictionaries

        Returns:
            List of unique endpoint URLs
        """
        from urllib.parse import urlparse

        endpoints = []
        for task in tasks:
            # Check common URL parameters
            for param in ["url", "uri", "dest", "src"]:
                if param in task and isinstance(task[param], str):
                    url = task[param]
                    # Extract just the base URL/domain
                    if url.startswith(("http://", "https://")):
                        # Extract domain from URL
                        parsed = urlparse(url)
                        endpoint = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        endpoints.append(endpoint)
        return list(set(endpoints))[:5]  # Limit to first 5 unique endpoints


class PortExtractor:
    """Extract network ports from tasks."""

    @staticmethod
    def extract(tasks: list[dict[str, Any]]) -> list[int]:
        """Extract network port numbers from tasks.

        Args:
            tasks: List of task dictionaries

        Returns:
            List of unique port numbers
        """
        ports = []
        for task in tasks:
            # Check common port parameters
            for param in ["port", "ports", "dest_port", "source_port"]:
                if param in task:
                    port_val = task[param]
                    if isinstance(port_val, int):
                        ports.append(port_val)
                    elif isinstance(port_val, str) and port_val.isdigit():
                        ports.append(int(port_val))
        return sorted(list(set(ports)))[:10]  # Limit to first 10 unique ports


class ServiceExtractor:
    """Extract service names from modules."""

    @staticmethod
    def extract(modules: list[str], int_type: Any) -> list[str]:
        """Extract service names based on integration type and modules used.

        Args:
            modules: List of module names
            int_type: Integration type

        Returns:
            List of service names
        """
        from ..models import IntegrationType

        services = []

        if int_type == IntegrationType.CLOUD:
            # Extract AWS services
            aws_services = {
                "ec2": "EC2",
                "s3": "S3",
                "rds": "RDS",
                "lambda": "Lambda",
                "iam": "IAM",
                "vpc": "VPC",
                "elb": "ELB",
                "cloudformation": "CloudFormation",
            }
            for module in modules:
                for key, service in aws_services.items():
                    if key in module.lower():
                        services.append(service)

            # Azure/GCP detection
            if any("azure" in m for m in modules):
                services.append("Azure")
            if any("gcp" in m or "google" in m for m in modules):
                services.append("GCP")

        elif int_type == IntegrationType.CONTAINER:
            if any("docker" in m for m in modules):
                services.append("Docker")
            if any("podman" in m for m in modules):
                services.append("Podman")
            if any("k8s" in m or "kubernetes" in m for m in modules):
                services.append("Kubernetes")

        elif int_type == IntegrationType.MONITORING:
            monitoring_map = {
                "datadog": "Datadog",
                "newrelic": "New Relic",
                "prometheus": "Prometheus",
                "grafana": "Grafana",
                "pagerduty": "PagerDuty",
                "nagios": "Nagios",
            }
            for module in modules:
                for key, service in monitoring_map.items():
                    if key in module.lower():
                        services.append(service)

        return list(set(services))
