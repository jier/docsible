"""
Special YAML handlers for Ansible-specific constructs.
"""
import yaml


def vault_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> str:
    """Handle Ansible Vault encrypted data in YAML files.

    Args:
        loader: YAML loader instance
        node: YAML node containing vault data

    Returns:
        Placeholder string for encrypted content
    """
    return "ENCRYPTED_WITH_ANSIBLE_VAULT"


# Register the custom constructor with the '!vault' tag.
yaml.SafeLoader.add_constructor('!vault', vault_constructor)
