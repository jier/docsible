"""
Integration boundary diagram generator for Ansible roles.

Generates Mermaid diagrams showing external system integrations and boundaries.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def generate_integration_boundary(integration_points: List) -> Optional[str]:
    """
    Generate system boundary diagram showing external integrations.

    Creates a Mermaid diagram showing:
    - Ansible role boundary
    - External systems (API, Database, Vault, etc.)
    - Integration direction and type
    - Credential requirements

    Args:
        integration_points: List of IntegrationPoint objects from complexity analyzer

    Returns:
        Mermaid diagram code as string, or None if no integrations

    Example:
        >>> from docsible.analyzers.complexity_analyzer import IntegrationPoint, IntegrationType
        >>> integrations = [
        ...     IntegrationPoint(
        ...         type=IntegrationType.API,
        ...         system_name="REST APIs",
        ...         modules_used=["uri"],
        ...         task_count=3,
        ...         uses_credentials=True
        ...     )
        ... ]
        >>> diagram = generate_integration_boundary(integrations)
        >>> print(diagram)
        graph LR
            Role[Ansible Role]
            API[REST APIs]
            Role -->|uri: 3 tasks| API
            API -.->|credentials| Role
    """
    if not integration_points:
        return None

    lines = ["graph LR"]
    lines.append("    Role[Ansible Role]")

    # Add external systems
    for idx, integration in enumerate(integration_points):
        system_id = f"{integration.type.value.upper()}{idx}"
        system_label = integration.system_name

        # Add system node with styling based on type
        if integration.type.value == "api":
            lines.append(f"    {system_id}[{system_label}]:::apiStyle")
        elif integration.type.value == "database":
            lines.append(f"    {system_id}[({system_label})]:::dbStyle")
        elif integration.type.value == "vault":
            lines.append(f"    {system_id}{{{{{system_label}}}}}:::vaultStyle")
        elif integration.type.value == "cloud":
            lines.append(f"    {system_id}[/{system_label}/]:::cloudStyle")
        elif integration.type.value == "network":
            lines.append(f"    {system_id}>{system_label}]:::networkStyle")
        elif integration.type.value == "container":
            lines.append(f"    {system_id}[{system_label}]:::containerStyle")
        elif integration.type.value == "monitoring":
            lines.append(f"    {system_id}[{system_label}]:::monitoringStyle")
        else:
            lines.append(f"    {system_id}[{system_label}]")

        # Add connection with module info
        modules_str = ", ".join(integration.modules_used[:2])  # Limit to 2 modules
        if len(integration.modules_used) > 2:
            modules_str += ", ..."
        label = f"{modules_str}: {integration.task_count} task{'s' if integration.task_count > 1 else ''}"

        lines.append(f"    Role -->|{label}| {system_id}")

        # Add credential flow if needed
        if integration.uses_credentials:
            lines.append(f"    {system_id} -.->|credentials| Role")

    # Add styling
    lines.append("")
    lines.append("    classDef apiStyle fill:#e1f5ff,stroke:#01579b,stroke-width:2px")
    lines.append("    classDef dbStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px")
    lines.append("    classDef vaultStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px")
    lines.append("    classDef cloudStyle fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px")
    lines.append(
        "    classDef networkStyle fill:#fce4ec,stroke:#c2185b,stroke-width:2px"
    )
    lines.append(
        "    classDef containerStyle fill:#e0f2f1,stroke:#00695c,stroke-width:2px"
    )
    lines.append(
        "    classDef monitoringStyle fill:#fff9c4,stroke:#f57f17,stroke-width:2px"
    )

    return "\n".join(lines)


def should_generate_integration_diagram(integration_points: List) -> bool:
    """
    Determine if an integration boundary diagram should be generated.

    Args:
        integration_points: List of IntegrationPoint objects

    Returns:
        True if diagram should be generated (2+ integration points or any with credentials)

    Example:
        >>> should_generate_integration_diagram([])
        False
        >>> should_generate_integration_diagram([mock_integration])  # 1 integration
        False
        >>> should_generate_integration_diagram([mock1, mock2])  # 2+ integrations
        True
    """
    if not integration_points:
        return False

    # Generate if 2+ integrations
    if len(integration_points) >= 2:
        return True

    # Generate if any integration uses credentials
    if any(ip.uses_credentials for ip in integration_points):
        return True

    return False
