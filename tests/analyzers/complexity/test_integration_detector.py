"""Tests for integration detection."""

from docsible.analyzers.complexity_analyzer import (
    IntegrationType,
    detect_integrations,
)


def test_detect_api_integration():
    """Test detection of API integrations."""
    role_info = {
        "tasks": [
            {
                "file": "api.yml",
                "tasks": [
                    {"name": "Call API", "module": "uri", "url_username": "user"},
                    {"name": "Download file", "module": "get_url", "token": "abc"},
                    {"name": "Process", "module": "debug"},
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.API
    assert integrations[0].system_name == "REST APIs"
    assert integrations[0].task_count == 2
    assert integrations[0].uses_credentials is True
    assert "uri" in integrations[0].modules_used
    assert "get_url" in integrations[0].modules_used


def test_detect_database_integration():
    """Test detection of database integrations."""
    role_info = {
        "tasks": [
            {
                "file": "database.yml",
                "tasks": [
                    {"name": "Create DB", "module": "postgresql_db"},
                    {
                        "name": "Create user",
                        "module": "postgresql_user",
                        "password": "secret",
                    },
                    {
                        "name": "Grant access",
                        "module": "community.postgresql.postgresql_privs",
                    },
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.DATABASE
    assert "PostgreSQL" in integrations[0].system_name
    assert integrations[0].task_count == 3
    assert integrations[0].uses_credentials is True


def test_detect_vault_integration():
    """Test detection of HashiCorp Vault integrations."""
    role_info = {
        "tasks": [
            {
                "file": "secrets.yml",
                "tasks": [
                    {
                        "name": "Read secret",
                        "module": "hashi_vault",
                        "vault_token": "token",
                    },
                    {
                        "name": "Write secret",
                        "module": "community.hashi_vault.vault_write",
                    },
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.VAULT
    assert integrations[0].system_name == "HashiCorp Vault"
    assert integrations[0].task_count == 2
    assert integrations[0].uses_credentials is True


def test_detect_multiple_integrations():
    """Test detection of multiple integration types."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "API call", "module": "uri"},
                    {
                        "name": "DB query",
                        "module": "mysql_db",
                        "login_password": "pass",
                    },
                    {"name": "Vault read", "module": "hashi_vault"},
                    {"name": "Regular task", "module": "debug"},
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    assert len(integrations) == 3

    types = {i.type for i in integrations}
    assert IntegrationType.API in types
    assert IntegrationType.DATABASE in types
    assert IntegrationType.VAULT in types


def test_exclude_composition_modules():
    """Test that role/task composition modules are excluded from integrations."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {
                        "name": "Include role",
                        "module": "include_role",
                        "role": "common",
                    },
                    {"name": "Import role", "module": "import_role", "role": "base"},
                    {
                        "name": "Include tasks",
                        "module": "include_tasks",
                        "file": "setup.yml",
                    },
                    {
                        "name": "Import tasks",
                        "module": "ansible.builtin.import_tasks",
                        "file": "cleanup.yml",
                    },
                    {"name": "API call", "module": "uri"},  # This should be detected
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    # Only the API call should be detected, not the composition modules
    assert len(integrations) == 1
    assert integrations[0].type == IntegrationType.API


def test_detect_no_integrations():
    """Test role with no external integrations."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Install package", "module": "apt"},
                    {"name": "Copy file", "module": "copy"},
                    {"name": "Template config", "module": "template"},
                ],
            }
        ],
    }

    integrations = detect_integrations(role_info)
    assert len(integrations) == 0
