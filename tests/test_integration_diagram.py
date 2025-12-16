"""Tests for integration boundary diagram generation."""

from docsible.analyzers.complexity_analyzer import IntegrationPoint, IntegrationType
from docsible.utils.integration_diagram import (
    generate_integration_boundary,
    should_generate_integration_diagram,
)


class TestIntegrationDiagram:
    """Test integration boundary diagram generation."""

    def test_generate_with_api_integration(self):
        """Test diagram generation with API integration."""
        integrations = [
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="REST APIs",
                modules_used=["uri", "get_url"],
                task_count=3,
                uses_credentials=True,
            )
        ]

        diagram = generate_integration_boundary(integrations)

        assert diagram is not None
        assert "graph LR" in diagram
        assert "REST APIs" in diagram
        assert "uri" in diagram
        assert "3 task" in diagram
        assert "credentials" in diagram
        assert "apiStyle" in diagram

    def test_generate_with_database_integration(self):
        """Test diagram generation with database integration."""
        integrations = [
            IntegrationPoint(
                type=IntegrationType.DATABASE,
                system_name="PostgreSQL Database",
                modules_used=["postgresql_db", "postgresql_user"],
                task_count=5,
                uses_credentials=True,
            )
        ]

        diagram = generate_integration_boundary(integrations)

        assert diagram is not None
        assert "PostgreSQL Database" in diagram
        assert "postgresql_db" in diagram
        assert "5 tasks" in diagram  # plural
        assert "dbStyle" in diagram

    def test_generate_with_vault_integration(self):
        """Test diagram generation with Vault integration."""
        integrations = [
            IntegrationPoint(
                type=IntegrationType.VAULT,
                system_name="HashiCorp Vault",
                modules_used=["hashi_vault"],
                task_count=2,
                uses_credentials=False,
            )
        ]

        diagram = generate_integration_boundary(integrations)

        assert diagram is not None
        assert "HashiCorp Vault" in diagram
        assert "vaultStyle" in diagram

    def test_generate_with_multiple_integrations(self):
        """Test diagram with multiple integration points."""
        integrations = [
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="REST APIs",
                modules_used=["uri"],
                task_count=2,
                uses_credentials=True,
            ),
            IntegrationPoint(
                type=IntegrationType.DATABASE,
                system_name="MySQL/MariaDB Database",
                modules_used=["mysql_db"],
                task_count=3,
                uses_credentials=True,
            ),
        ]

        diagram = generate_integration_boundary(integrations)

        assert diagram is not None
        assert "REST APIs" in diagram
        assert "MySQL/MariaDB Database" in diagram
        # Should have 2 credential flows
        assert diagram.count("credentials") == 2

    def test_generate_with_many_modules(self):
        """Test module name truncation for readability."""
        integrations = [
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="REST APIs",
                modules_used=[
                    "uri",
                    "get_url",
                    "ansible.builtin.uri",
                    "custom_api_module",
                ],
                task_count=10,
                uses_credentials=False,
            )
        ]

        diagram = generate_integration_boundary(integrations)

        assert diagram is not None
        # Should truncate modules list with "..."
        assert "..." in diagram

    def test_generate_empty_integrations(self):
        """Test that empty integration list returns None."""
        diagram = generate_integration_boundary([])
        assert diagram is None

    def test_should_generate_with_no_integrations(self):
        """Test decision logic with no integrations."""
        assert should_generate_integration_diagram([]) is False

    def test_should_generate_with_one_integration_no_creds(self):
        """Test decision logic with single integration, no credentials."""
        integrations = [
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="REST APIs",
                modules_used=["uri"],
                task_count=1,
                uses_credentials=False,
            )
        ]
        assert should_generate_integration_diagram(integrations) is False

    def test_should_generate_with_one_integration_with_creds(self):
        """Test decision logic with single integration that uses credentials."""
        integrations = [
            IntegrationPoint(
                type=IntegrationType.DATABASE,
                system_name="PostgreSQL",
                modules_used=["postgresql_db"],
                task_count=1,
                uses_credentials=True,
            )
        ]
        assert should_generate_integration_diagram(integrations) is True

    def test_should_generate_with_multiple_integrations(self):
        """Test decision logic with 2+ integrations."""
        integrations = [
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="API 1",
                modules_used=["uri"],
                task_count=1,
                uses_credentials=False,
            ),
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="API 2",
                modules_used=["get_url"],
                task_count=1,
                uses_credentials=False,
            ),
        ]
        assert should_generate_integration_diagram(integrations) is True

    def test_diagram_syntax_valid(self):
        """Test that generated diagram has valid Mermaid syntax."""
        integrations = [
            IntegrationPoint(
                type=IntegrationType.API,
                system_name="Test API",
                modules_used=["uri"],
                task_count=1,
                uses_credentials=True,
            )
        ]

        diagram = generate_integration_boundary(integrations)

        # Check basic Mermaid syntax
        assert diagram.startswith("graph LR")
        assert "Role[Ansible Role]" in diagram
        assert "-->" in diagram  # Connection
        assert "-.->|credentials|" in diagram  # Credential flow
        assert "classDef" in diagram  # Styling definitions
