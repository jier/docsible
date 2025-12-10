"""
Mermaid diagram formatting utilities.
"""
import logging
import re

logger = logging.getLogger(__name__)


def sanitize_for_mermaid_id(text: str) -> str:
    """Sanitize text to create a valid Mermaid diagram node ID.

    Replaces pipes with underscores and removes non-alphanumeric characters
    (except French accents).

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for use as Mermaid node ID

    Example:
        >>> sanitize_for_mermaid_id("Install | nginx-1.0")
        'Install___nginx_1_0'
    """
    text = text.replace("|", "_")
    # Allowing a-zA-Z0-9 as well as French accents
    return re.sub(r'[^a-zA-Z0-9À-ÿ]', '_', text)


def break_text(text: str, max_length: int = 50) -> str:
    """Break long text into multiple lines for better display in diagrams.

    Splits text at word boundaries to fit within max_length and joins with HTML <br> tags.

    Args:
        text: Text to break into lines
        max_length: Maximum length per line (default: 50)

    Returns:
        Text with <br> tags inserted for line breaks

    Example:
        >>> break_text("This is a very long text that needs wrapping", 20)
        'This is a very long<br>text that needs<br>wrapping'
    """
    words = text.split(' ')
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if current_length + len(word) + len(current_line) > max_length:
            lines.append(' '.join(current_line))
            current_length = 0
            current_line = []
        current_line.append(word)
        current_length += len(word)
    if current_line:
        lines.append(' '.join(current_line))
    return '<br>'.join(lines)


def sanitize_for_title(text: str) -> str:
    """Sanitize text for use as diagram title.

    Converts to lowercase, replaces special characters with spaces,
    and breaks into multiple lines if needed.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized and formatted text, or "cannot handle" if error occurs

    Example:
        >>> sanitize_for_title("Install Package: nginx-1.0")
        'install package nginx 1 0'
    """
    # Allowing a-z0-9 as well as French accents, and converting to lower case
    try:
        sanitized_text = re.sub(r'[^a-z0-9À-ÿ]', ' ', text.lower())
        return break_text(sanitized_text)
    except Exception as e:
        logger.warning(f"Failed to sanitize title '{text}': {e}")
        return "cannot handle"


def sanitize_for_condition(text: str, max_length: int = 50) -> str:
    """Sanitize conditional expression for display in diagrams.

    Converts to lowercase, replaces special characters with spaces,
    and breaks into lines at max_length.

    Args:
        text: Conditional expression to sanitize
        max_length: Maximum length per line (default: 50)

    Returns:
        Sanitized and formatted conditional text

    Example:
        >>> sanitize_for_condition("ansible_os_family == 'RedHat'")
        'ansible os family redhat'
    """
    sanitized_text = re.sub(r'[^a-z0-9À-ÿ]', ' ', text.lower())
    return break_text(sanitized_text, max_length)
