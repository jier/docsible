"""Formatting utilities for Mermaid diagrams.

This module provides utility functions for sanitizing and formatting text
for use in Mermaid diagrams.
"""

import logging
import re

logger = logging.getLogger(__name__)


def sanitize_for_id(text: str) -> str:
    """Sanitize text to create a valid Mermaid diagram node ID.

    Replaces special characters with underscores to create safe node IDs
    that can be used in Mermaid diagrams.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for use as Mermaid node ID

    Example:
        >>> sanitize_for_id("Install | nginx-1.0")
        'Install___nginx_1_0'
        >>> sanitize_for_id("Task with spaces")
        'Task_with_spaces'
    """
    # Replace pipes with underscores
    text = text.replace("|", "_")
    # Replace other special characters with underscores (keep French accents)
    text = re.sub(r"[^a-zA-Z0-9À-ÿ]", "_", text)
    # Remove consecutive underscores
    text = re.sub(r"_+", "_", text)
    # Remove leading/trailing underscores
    text = text.strip("_")
    return text


def break_text(text: str, max_length: int = 50) -> str:
    """Break long text into multiple lines for better display in diagrams.

    Splits text at word boundaries to fit within max_length and joins
    with HTML <br> tags for Mermaid diagram display.

    Args:
        text: Text to break into lines
        max_length: Maximum length per line (default: 50)

    Returns:
        Text with <br> tags inserted for line breaks

    Example:
        >>> break_text("This is a very long text that needs wrapping", 20)
        'This is a very long<br>text that needs<br>wrapping'
    """
    if len(text) <= max_length:
        return text

    words = text.split(" ")
    lines: list[str] = []
    current_line: list[str] = []
    current_length = 0

    for word in words:
        word_length = len(word)
        # Check if adding this word would exceed max_length
        if current_length + word_length + len(current_line) > max_length:
            if current_line:  # Only add if line is not empty
                lines.append(" ".join(current_line))
                current_line = []
                current_length = 0

        current_line.append(word)
        current_length += word_length

    if current_line:
        lines.append(" ".join(current_line))

    return "<br>".join(lines)


def sanitize_for_title(text: str, max_length: int = 50) -> str:
    """Sanitize text for use as diagram title.

    Converts to lowercase, replaces special characters with spaces,
    and breaks into multiple lines if needed.

    Args:
        text: Text to sanitize
        max_length: Maximum line length (default: 50)

    Returns:
        Sanitized and formatted text, or "cannot handle" if error occurs

    Example:
        >>> sanitize_for_title("Install Package: nginx-1.0")
        'install package nginx 1 0'
    """
    try:
        # Convert to lowercase and replace special chars with spaces (keep French accents)
        sanitized_text = re.sub(r"[^a-z0-9À-ÿ]", " ", text.lower())
        # Remove multiple consecutive spaces
        sanitized_text = re.sub(r"\s+", " ", sanitized_text).strip()
        return break_text(sanitized_text, max_length)
    except Exception as e:
        logger.warning(f"Failed to sanitize title '{text}': {e}")
        return "cannot handle"


def sanitize_for_condition(text: str, max_length: int = 50) -> str:
    """Sanitize conditional expression for display in diagrams.

    Converts to lowercase, replaces special characters with spaces,
    and breaks into lines at max_length.

    Args:
        text: Conditional expression to sanitize
        max_length: Maximum line length (default: 50)

    Returns:
        Sanitized conditional expression

    Example:
        >>> sanitize_for_condition("ansible_os_family == 'Debian'")
        'ansible os family debian'
    """
    try:
        # Convert to lowercase and replace special chars with spaces (keep French accents)
        sanitized_text = re.sub(r"[^a-z0-9À-ÿ]", " ", text.lower())
        # Remove multiple consecutive spaces
        sanitized_text = re.sub(r"\s+", " ", sanitized_text).strip()
        return break_text(sanitized_text, max_length)
    except Exception as e:
        logger.warning(f"Failed to sanitize condition '{text}': {e}")
        return text


def escape_pipes(text: str) -> str:
    """Escape pipe characters for Mermaid diagram compatibility.

    Replaces '|' with '¦' to prevent syntax issues in Mermaid diagrams.

    Args:
        text: Text with potential pipe characters

    Returns:
        Text with escaped pipes

    Example:
        >>> escape_pipes("command | grep text")
        'command ¦ grep text'
    """
    return text.replace("|", "¦")


def truncate_text(text: str, max_length: int = 40, suffix: str = "...") -> str:
    """Truncate text to maximum length with optional suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length (default: 40)
        suffix: Suffix to add when truncated (default: "...")

    Returns:
        Truncated text with suffix if needed

    Example:
        >>> truncate_text("This is a very long task name", 20)
        'This is a very lo...'
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def quote_for_label(text: str) -> str:
    """Quote text for use as Mermaid edge label.

    Adds quotes around text and escapes internal quotes.

    Args:
        text: Text to quote

    Returns:
        Quoted text safe for use as label

    Example:
        >>> quote_for_label("Task's name")
        '"Task\'s name"'
    """
    # Escape existing quotes
    text = text.replace('"', '\\"')
    return f'"{text}"'
