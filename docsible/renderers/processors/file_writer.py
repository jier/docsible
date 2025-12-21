import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileWriter:
    """Handles file writing with consistent encoding.

    Provides a centralized interface for writing rendered content to files
    with proper encoding and logging.
    """

    def write(self, output_path: Path, content: str) -> None:
        """Write content to file with UTF-8 encoding.

        Creates parent directories if they don't exist and writes the content
        with UTF-8 encoding. Logs success message after writing.

        Args:
            output_path: Path where content will be written
            content: Content to write to file

        Raises:
            OSError: If file cannot be written due to permissions or disk space
            UnicodeEncodeError: If content contains invalid UTF-8 characters

        Example:
            >>> writer = FileWriter()
            >>> writer.write(Path('README.md'), '# My Role\\n\\nContent here')
        """
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file with UTF-8 encoding
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"✓ README written at: {output_path}")
