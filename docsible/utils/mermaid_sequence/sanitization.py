"""
Text sanitization utilities for Mermaid sequence diagrams.
"""

import re


def sanitize_participant_name(text: str) -> str:
    """Sanitize text to be used as a Mermaid participant name.

    Removes special characters, keeping only alphanumeric and underscores.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for use as Mermaid participant name

    Example:
        >>> sanitize_participant_name("my-role.name")
        'my_role_name'
    """
    # Remove special characters, keep alphanumeric and underscores
    return re.sub(r"[^a-zA-Z0-9_]", "_", text)


def sanitize_note_text(text: str, max_length: int = 50) -> str:
    """Sanitize text for use in notes and messages.

    Truncates to max_length and escapes special characters.

    Args:
        text: Text to sanitize
        max_length: Maximum length before truncation (default: 50)

    Returns:
        Sanitized text safe for use in Mermaid notes/messages

    Example:
        >>> sanitize_note_text('Long text with "quotes"\\nand newlines', 20)
        'Long text with \\'quote...'
    """
    # Truncate and escape special characters
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text.replace('"', "'").replace("\n", " ")
