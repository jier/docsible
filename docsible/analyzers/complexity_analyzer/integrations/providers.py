"""Provider detection for cloud, database, container platforms."""

from typing import Any

from ..models import IntegrationPoint, IntegrationType


class BaseIntegrationDetector:
    """Base class for integration detectors."""

    def detect(self, role_info: dict[str, Any]) -> list[IntegrationPoint]:
        """Detect integrations in role.

        Args:
            role_info: Role information dictionary

        Returns:
            List of detected integration points
        """
        raise NotImplementedError


class CloudProviderDetector(BaseIntegrationDetector):
    """Detect cloud provider integrations."""

    CLOUD_MODULES = [
        "aws_",
        "amazon.aws",
        "ec2",
        "s3",
        "rds",
        "lambda",  # AWS
        "azure_",
        "azure.azcollection",  # Azure
        "gcp_",
        "google.cloud",  # GCP
        "openstack",
        "os_",  # OpenStack
    ]

    def detect(self, role_info: dict[str, Any]) -> list[IntegrationPoint]:
        """Detect cloud integrations."""
        tasks = self._collect_matching_tasks(role_info, self.CLOUD_MODULES)
        if not tasks:
            return []

        modules_used = list(set(t["module"] for t in tasks))
        system_name = self._detect_cloud_provider(modules_used)

        from .extractors import ServiceExtractor

        services = ServiceExtractor.extract(modules_used, IntegrationType.CLOUD)

        return [
            IntegrationPoint(
                type=IntegrationType.CLOUD,
                system_name=system_name,
                modules_used=modules_used,
                task_count=len(tasks),
                uses_credentials=any(self._task_uses_credentials(t["task"]) for t in tasks),
                services=services,
            )
        ]

    def _collect_matching_tasks(
        self, role_info: dict[str, Any], patterns: list[str]
    ) -> list[dict[str, Any]]:
        """Collect tasks matching module patterns."""
        matching = []
        for task_file_info in role_info.get("tasks", []):
            for task in task_file_info.get("tasks", []):
                module = task.get("module", "")
                if any(module.startswith(p) or p in module for p in patterns):
                    matching.append({"module": module, "task": task})
        return matching

    def _task_uses_credentials(self, task: dict[str, Any]) -> bool:
        """Check if task uses credential-related parameters."""
        credential_params = [
            "username",
            "password",
            "api_key",
            "token",
            "auth",
            "authorization",
            "user",
        ]
        return any(param in task for param in credential_params)

    def _detect_cloud_provider(self, modules: list[str]) -> str:
        """Detect specific cloud provider from modules."""
        if any("aws" in m or "ec2" in m or "s3" in m or "amazon" in m for m in modules):
            return "AWS (Amazon Web Services)"
        elif any("azure" in m for m in modules):
            return "Microsoft Azure"
        elif any("gcp" in m or "google.cloud" in m for m in modules):
            return "Google Cloud Platform"
        elif any("openstack" in m for m in modules):
            return "OpenStack"
        else:
            return "Cloud Provider"


class DatabaseDetector(BaseIntegrationDetector):
    """Detect database integrations."""

    DATABASE_MODULES = [
        "mysql",
        "mysql_",
        "postgresql",
        "postgresql_",
        "mongodb",
        "mongodb_",
        "community.mysql",
        "community.postgresql",
        "community.mongodb",
    ]

    def detect(self, role_info: dict[str, Any]) -> list[IntegrationPoint]:
        """Detect database integrations."""
        tasks = self._collect_matching_tasks(role_info, self.DATABASE_MODULES)
        if not tasks:
            return []

        modules_used = list(set(t["module"] for t in tasks))
        system_name = self._detect_database_type(modules_used)

        return [
            IntegrationPoint(
                type=IntegrationType.DATABASE,
                system_name=system_name,
                modules_used=modules_used,
                task_count=len(tasks),
                uses_credentials=any(self._task_uses_credentials(t["task"]) for t in tasks),
            )
        ]

    def _collect_matching_tasks(
        self, role_info: dict[str, Any], patterns: list[str]
    ) -> list[dict[str, Any]]:
        """Collect tasks matching module patterns."""
        matching = []
        for task_file_info in role_info.get("tasks", []):
            for task in task_file_info.get("tasks", []):
                module = task.get("module", "")
                if any(module.startswith(p) for p in patterns):
                    matching.append({"module": module, "task": task})
        return matching

    def _task_uses_credentials(self, task: dict[str, Any]) -> bool:
        """Check if task uses credential-related parameters."""
        credential_params = ["username", "password", "login_password", "user"]
        return any(param in task for param in credential_params)

    def _detect_database_type(self, modules: list[str]) -> str:
        """Detect specific database type from modules."""
        if any("postgresql" in m for m in modules):
            return "PostgreSQL Database"
        elif any("mysql" in m for m in modules):
            return "MySQL/MariaDB Database"
        elif any("mongodb" in m for m in modules):
            return "MongoDB Database"
        else:
            return "Database"


class ContainerDetector(BaseIntegrationDetector):
    """Detect container platform integrations."""

    CONTAINER_MODULES = [
        "docker",
        "docker_",
        "community.docker",  # Docker
        "podman",
        "containers.podman",  # Podman
        "kubernetes",
        "k8s",
        "community.kubernetes",  # Kubernetes
    ]

    def detect(self, role_info: dict[str, Any]) -> list[IntegrationPoint]:
        """Detect container integrations."""
        tasks = self._collect_matching_tasks(role_info, self.CONTAINER_MODULES)
        if not tasks:
            return []

        modules_used = list(set(t["module"] for t in tasks))
        system_name = self._detect_container_platform(modules_used)

        from .extractors import ServiceExtractor

        services = ServiceExtractor.extract(modules_used, IntegrationType.CONTAINER)

        return [
            IntegrationPoint(
                type=IntegrationType.CONTAINER,
                system_name=system_name,
                modules_used=modules_used,
                task_count=len(tasks),
                uses_credentials=any(self._task_uses_credentials(t["task"]) for t in tasks),
                services=services,
            )
        ]

    def _collect_matching_tasks(
        self, role_info: dict[str, Any], patterns: list[str]
    ) -> list[dict[str, Any]]:
        """Collect tasks matching module patterns."""
        matching = []
        for task_file_info in role_info.get("tasks", []):
            for task in task_file_info.get("tasks", []):
                module = task.get("module", "")
                if any(module.startswith(p) or p in module for p in patterns):
                    matching.append({"module": module, "task": task})
        return matching

    def _task_uses_credentials(self, task: dict[str, Any]) -> bool:
        """Check if task uses credential-related parameters."""
        credential_params = ["username", "password", "token"]
        return any(param in task for param in credential_params)

    def _detect_container_platform(self, modules: list[str]) -> str:
        """Detect specific container platform from modules."""
        if any("kubernetes" in m or "k8s" in m for m in modules):
            return "Kubernetes"
        elif any("docker" in m for m in modules):
            return "Docker"
        elif any("podman" in m for m in modules):
            return "Podman"
        else:
            return "Container Platform"


class MonitoringDetector(BaseIntegrationDetector):
    """Detect monitoring system integrations."""

    MONITORING_MODULES = [
        "datadog",
        "newrelic",  # APM
        "prometheus",
        "grafana",  # Metrics
        "pagerduty",
        "opsgenie",  # Alerting
        "nagios",
        "zabbix",  # Monitoring
    ]

    def detect(self, role_info: dict[str, Any]) -> list[IntegrationPoint]:
        """Detect monitoring integrations."""
        tasks = self._collect_matching_tasks(role_info, self.MONITORING_MODULES)
        if not tasks:
            return []

        modules_used = list(set(t["module"] for t in tasks))
        system_name = self._detect_monitoring_platform(modules_used)

        from .extractors import ServiceExtractor

        services = ServiceExtractor.extract(modules_used, IntegrationType.MONITORING)

        return [
            IntegrationPoint(
                type=IntegrationType.MONITORING,
                system_name=system_name,
                modules_used=modules_used,
                task_count=len(tasks),
                uses_credentials=any(self._task_uses_credentials(t["task"]) for t in tasks),
                services=services,
            )
        ]

    def _collect_matching_tasks(
        self, role_info: dict[str, Any], patterns: list[str]
    ) -> list[dict[str, Any]]:
        """Collect tasks matching module patterns."""
        matching = []
        for task_file_info in role_info.get("tasks", []):
            for task in task_file_info.get("tasks", []):
                module = task.get("module", "")
                if any(p in module.lower() for p in patterns):
                    matching.append({"module": module, "task": task})
        return matching

    def _task_uses_credentials(self, task: dict[str, Any]) -> bool:
        """Check if task uses credential-related parameters."""
        credential_params = ["api_key", "token", "auth"]
        return any(param in task for param in credential_params)

    def _detect_monitoring_platform(self, modules: list[str]) -> str:
        """Detect specific monitoring platform from modules."""
        if any("datadog" in m for m in modules):
            return "Datadog"
        elif any("prometheus" in m for m in modules):
            return "Prometheus"
        elif any("grafana" in m for m in modules):
            return "Grafana"
        elif any("newrelic" in m for m in modules):
            return "New Relic"
        elif any("nagios" in m for m in modules):
            return "Nagios"
        elif any("zabbix" in m for m in modules):
            return "Zabbix"
        else:
            return "Monitoring Platform"
