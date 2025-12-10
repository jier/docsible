"""
Network topology diagram generator for Ansible roles.

Generates detailed network diagrams showing ports, protocols, and firewall rules.
"""

import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


def generate_network_topology(integration_points: List) -> Optional[str]:
    """
    Generate network topology diagram for roles with network integrations.

    Creates a Mermaid diagram showing:
    - Network zones/segments
    - Firewall rules and ports
    - Protocol information
    - Connection flows

    Args:
        integration_points: List of IntegrationPoint objects from complexity analyzer

    Returns:
        Mermaid diagram code as string, or None if no network integrations
    """
    # Filter for network integrations only
    network_integrations = [
        ip for ip in integration_points
        if ip.type.value == 'network'
    ]

    if not network_integrations:
        return None

    lines = ["graph TB"]
    lines.append("    subgraph Network Infrastructure")

    for idx, integration in enumerate(network_integrations):
        node_id = f"NET{idx}"

        # Create node with port information
        port_info = ""
        if integration.ports:
            ports_str = ", ".join(str(p) for p in integration.ports[:5])
            if len(integration.ports) > 5:
                ports_str += "..."
            port_info = f"<br/>Ports: {ports_str}"

        lines.append(f"        {node_id}[\"{integration.system_name}{port_info}\"]:::netNode")

        # Add module information
        for module in integration.modules_used[:3]:
            module_id = f"MOD{idx}_{module.replace('.', '_')}"
            lines.append(f"        {module_id}[{module}]:::moduleNode")
            lines.append(f"        {module_id} --> {node_id}")

    lines.append("    end")

    # Add styling
    lines.append("")
    lines.append("    classDef netNode fill:#fce4ec,stroke:#c2185b,stroke-width:2px")
    lines.append("    classDef moduleNode fill:#fff,stroke:#666,stroke-width:1px,stroke-dasharray: 5 5")

    return "\n".join(lines)


def should_generate_network_topology(integration_points: List) -> bool:
    """
    Determine if a network topology diagram should be generated.

    Args:
        integration_points: List of IntegrationPoint objects

    Returns:
        True if role has network integrations with port information
    """
    if not integration_points:
        return False

    # Check for network integrations
    network_integrations = [
        ip for ip in integration_points
        if ip.type.value == 'network'
    ]

    # Generate if we have network integrations
    return len(network_integrations) > 0


def format_integration_details(integration_point: Any) -> Dict[str, str]:
    """
    Format integration-specific details for documentation.

    Extracts and formats type-specific information like endpoints, ports, services.

    Args:
        integration_point: IntegrationPoint object

    Returns:
        Dictionary of formatted details
    """
    details = {}

    # API details
    if integration_point.type.value == 'api' and integration_point.endpoints:
        details['endpoints'] = integration_point.endpoints

    # Network details
    if integration_point.type.value == 'network' and integration_point.ports:
        details['ports'] = [str(p) for p in integration_point.ports]

    # Cloud/Container/Monitoring details
    if integration_point.services:
        details['services'] = integration_point.services

    return details
