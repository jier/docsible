"""Contextual help provider for error-specific guidance."""


class ContextualHelpProvider:
    """Provide context-specific help messages based on error types."""

    ERROR_HELP: dict[str, dict[str, str]] = {
        "RoleNotFoundError": {
            "message": "Role directory not found",
            "help": """
Common Solutions:

1. Check the path exists:
   ls -la /path/to/role

2. Make sure you're in the right directory:
   cd /path/to/role
   docsible role --role .

3. For roles in collections:
   docsible role --collection /path/to/collection

Learn more: docsible guide troubleshooting
""",
        },
        "ClickException": {
            "message": "Command error",
            "help": """
Quick Help:
   docsible role --help          # Show essential options
   docsible role --help-full     # Show all options
   docsible guide getting-started # Interactive guide
""",
        },
        "FileNotFoundError": {
            "message": "File not found",
            "help": """
Common Solutions:

1. Verify the file path is correct
2. Check you have read permissions
3. For role paths, use absolute paths:
   docsible role --role /absolute/path/to/role

Learn more: docsible guide troubleshooting
""",
        },
    }

    @classmethod
    def get_help(cls, error_type: str) -> str | None:
        """Get contextual help text for an error type.

        Args:
            error_type: Exception class name

        Returns:
            Help text string, or None if no specific help
        """
        return cls.ERROR_HELP.get(error_type, {}).get("help")

    @classmethod
    def format_error_with_help(cls, error: Exception) -> str:
        """Format an error message with contextual help.

        Args:
            error: The exception that occurred

        Returns:
            Formatted error string with contextual help if available
        """
        error_type = type(error).__name__
        help_text = cls.get_help(error_type)

        if help_text:
            return f"Error: {error}\n{help_text}"
        return f"Error: {error}"

    @classmethod
    def get_supported_error_types(cls) -> list[str]:
        """Return list of error types with specific help."""
        return list(cls.ERROR_HELP.keys())
