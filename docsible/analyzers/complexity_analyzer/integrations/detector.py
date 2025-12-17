"""Main integration detection orchestrator."""

from typing import Any

from ..models import IntegrationType, IntegrationPoint
from .extractors import EndpointExtractor, PortExtractor
from .providers import (
    BaseIntegrationDetector,
    CloudProviderDetector,
    ContainerDetector,
    DatabaseDetector,
    MonitoringDetector,
)


class APIDetector(BaseIntegrationDetector):
    """Detect API integrations."""

    API_MODULES = ["uri", "get_url", "ansible.builtin.uri", "ansible.builtin.get_url"]

    def detect(self, role_info: dict[str, Any]) -> list[IntegrationPoint]:
        """Detect API integrations."""
        tasks = []
        for task_file_info in role_info.get("tasks", []):
            for task in task_file_info.get("tasks", []):
                module = task.get("module", "")
                if module in self.API_MODULES:
                    tasks.append({"module": module, "task": task})

        if not tasks:
            return []

        modules_used = list(set(t["module"] for t in tasks))
        endpoints = EndpointExtractor.extract([t["task"] for t in tasks])

        return [
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="REST APIs",
                modules_used=modules_used,
                task_count=len(tasks),
                uses_credentials=any(self._task_uses_credentials(t["task"]) for t in tasks),
                endpoints=endpoints,
            )
        ]

    def _task_uses_credentials(self, task: dict[str, Any]) -> bool:
        """Check if task uses credential-related parameters."""
        credential_params = [
            "url_username",
            "url_password",
            "user",
            "password",
            "token",
            "headers",
        ]
        return any(param in task for param in credential_params)


class VaultDetector(BaseIntegrationDetector):
    """Detect Vault integrations."""

    VAULT_MODULES = ["hashi_vault", "community.hashi_vault"]

    def detect(self, role_info: dict[str, Any]) -> list[IntegrationPoint]:
        """Detect Vault integrations."""
        tasks = []
        for task_file_info in role_info.get("tasks", []):
            for task in task_file_info.get("tasks", []):
                module = task.get("module", "")
                if any(v in module for v in self.VAULT_MODULES):
                    tasks.append({"module": module, "task": task})

        if not tasks:
            return []

        modules_used = list(set(t["module"] for t in tasks))

        return [
            IntegrationPoint(
                type=IntegrationType.VAULT,
                system_name="HashiCorp Vault",
                modules_used=modules_used,
                task_count=len(tasks),
                uses_credentials=True,  # Vault always requires credentials
            )
        ]


class NetworkDetector(BaseIntegrationDetector):
    """Detect network infrastructure integrations."""

    NETWORK_MODULES = [
        "firewalld",
        "iptables",
        "ufw",  # Firewall
        "nmcli",
        "network",
        "route",  # Network config
        "cisco",
        "junos",
        "vyos",  # Network devices
        "ansible.builtin.iptables",
        "community.general.ufw",
    ]

    def detect(self, role_info: dict[str, Any]) -> list[IntegrationPoint]:
        """Detect network integrations."""
        tasks = []
        for task_file_info in role_info.get("tasks", []):
            for task in task_file_info.get("tasks", []):
                module = task.get("module", "")
                if any(module.startswith(net) or net in module for net in self.NETWORK_MODULES):
                    tasks.append({"module": module, "task": task})

        if not tasks:
            return []

        modules_used = list(set(t["module"] for t in tasks))
        ports = PortExtractor.extract([t["task"] for t in tasks])

        return [
            IntegrationPoint(
                type=IntegrationType.NETWORK,
                system_name="Network Infrastructure",
                modules_used=modules_used,
                task_count=len(tasks),
                uses_credentials=any(self._task_uses_credentials(t["task"]) for t in tasks),
                ports=ports,
            )
        ]

    def _task_uses_credentials(self, task: dict[str, Any]) -> bool:
        """Check if task uses credential-related parameters."""
        credential_params = ["username", "password", "auth"]
        return any(param in task for param in credential_params)


class IntegrationDetector:
    """Orchestrates all integration detection with pluggable architecture.

    Supports custom detectors via register_detector() method.

    Example:
        # Use defaults
        detector = IntegrationDetector()
        integrations = detector.detect_integrations(role_info)

        # Add custom detector
        class CustomDetector(BaseIntegrationDetector):
            def detect(self, role_info):
                return [...]

        detector = IntegrationDetector()
        detector.register_detector(CustomDetector())
        integrations = detector.detect_integrations(role_info)
    """

    # Ansible composition modules to exclude from integration detection
    COMPOSITION_MODULES = [
        "include_role",
        "import_role",
        "include_tasks",
        "import_tasks",
        "ansible.builtin.include_role",
        "ansible.builtin.import_role",
        "ansible.builtin.include_tasks",
        "ansible.builtin.import_tasks",
    ]

    def __init__(self) -> None:
        """Initialize with default detectors."""
        self._detectors: list[BaseIntegrationDetector] = [
            APIDetector(),
            DatabaseDetector(),
            VaultDetector(),
            CloudProviderDetector(),
            NetworkDetector(),
            ContainerDetector(),
            MonitoringDetector(),
        ]

    def register_detector(self, detector: BaseIntegrationDetector) -> None:
        """Register a custom integration detector.

        Args:
            detector: Custom detector implementing BaseIntegrationDetector

        Example:
            >>> detector = IntegrationDetector()
            >>> detector.register_detector(MyCustomDetector())
        """
        self._detectors.append(detector)

    def detect_integrations(self, role_info: dict[str, Any]) -> list[IntegrationPoint]:
        """Detect all external system integrations in role.

        Excludes Ansible composition modules (include_role, include_tasks, etc.).

        Args:
            role_info: Role information dictionary from build_role_info()

        Returns:
            List of detected integration points

        Example:
            >>> detector = IntegrationDetector()
            >>> integrations = detector.detect_integrations(role_info)
            >>> for integration in integrations:
            ...     print(f"{integration.system_name}: {integration.task_count} tasks")
        """
        all_integrations = []

        # Run all registered detectors
        for detector in self._detectors:
            try:
                integrations = detector.detect(role_info)
                all_integrations.extend(integrations)
            except Exception:
                # Continue with other detectors if one fails
                continue

        return all_integrations


# Backward compatibility: provide function-based API
def detect_integrations(role_info: dict[str, Any]) -> list[IntegrationPoint]:
    """Detect external system integrations by analyzing task modules.

    This is a convenience function that uses the default IntegrationDetector.
    For custom detectors, use IntegrationDetector class directly.

    Args:
        role_info: Role information dictionary

    Returns:
        List of detected integration points

    Example:
        >>> integrations = detect_integrations(role_info)
        >>> for integration in integrations:
        ...     print(f"{integration.system_name}: {integration.task_count} tasks")
    """
    detector = IntegrationDetector()
    return detector.detect_integrations(role_info)
