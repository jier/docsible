"""Custom exceptions for Docsible.

This module defines the exception hierarchy for Docsible, providing
specific exception types for different error scenarios.
"""


class DocsibleError(Exception):
    """Base exception for all Docsible errors.

    All custom Docsible exceptions should inherit from this base class
    to allow for easy catching of all Docsible-specific errors.
    """

    pass


class ConfigurationError(DocsibleError):
    """Error in configuration file or project structure.

    Raised when:
    - .docsible.yml has invalid syntax or values
    - Required configuration is missing
    - Directory structure is invalid
    - Path validation fails

    Example:
        raise ConfigurationError("Invalid defaults_dir: must not start with '/'")
    """

    pass


class RoleNotFoundError(DocsibleError):
    """Role directory not found or invalid.

    Raised when:
    - Specified role path doesn't exist
    - Path is not a directory
    - Role has no required structure (tasks/, defaults/, etc.)

    Example:
        raise RoleNotFoundError(f"Role not found at: {role_path}")
    """

    pass


class CollectionNotFoundError(DocsibleError):
    """Collection directory not found or invalid.

    Raised when:
    - No galaxy.yml/galaxy.yaml found
    - Collection structure is invalid
    - Required metadata is missing

    Example:
        raise CollectionNotFoundError("No galaxy.yml found in collection")
    """

    pass


class TemplateRenderError(DocsibleError):
    """Error rendering Jinja2 template.

    Raised when:
    - Template syntax is invalid
    - Template file not found
    - Template rendering fails
    - Required template variables missing

    Example:
        raise TemplateRenderError(f"Failed to render {template_name}: {error}")
    """

    pass


class YAMLParseError(DocsibleError):
    """Error parsing YAML file.

    Raised when:
    - YAML syntax is invalid
    - File encoding is wrong
    - YAML structure doesn't match expected format

    Example:
        raise YAMLParseError(f"Invalid YAML in {file_path}: {error}")
    """

    pass


class GitOperationError(DocsibleError):
    """Error during Git operations.

    Raised when:
    - Git repository detection fails
    - Git command execution fails
    - Repository information cannot be extracted

    Example:
        raise GitOperationError("Failed to detect Git repository")
    """

    pass


class MermaidGenerationError(DocsibleError):
    """Error generating Mermaid diagrams.

    Raised when:
    - Diagram generation fails
    - Invalid diagram syntax produced
    - Task structure incompatible with diagram type

    Example:
        raise MermaidGenerationError(f"Failed to generate diagram: {error}")
    """

    pass
