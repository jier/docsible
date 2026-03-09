"""Network configuration concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector
from docsible.analyzers.shared.module_taxonomy import NETWORK_MODULES


class NetworkConfigurationConcern(ConcernDetector):
    """Detects network and firewall configuration tasks."""

    @property
    def concern_name(self) -> str:
        return "network_configuration"

    @property
    def display_name(self) -> str:
        return "Network Configuration"

    @property
    def description(self) -> str:
        return "Managing network settings, firewall rules, and routing"

    @property
    def module_patterns(self) -> list:
        # dns is network-specific and not in the shared taxonomy
        return sorted(NETWORK_MODULES) + ["dns"]

    @property
    def suggested_filename(self) -> str:
        return "network.yml"

    @property
    def priority(self) -> int:
        return 45
