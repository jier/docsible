import logging
from pathlib import Path

from docsible.utils.metadata import generate_metadata

logger = logging.getLogger(__name__)


class MetadataProcessor:
    """Handles metadata generation and injection.

    Generates metadata about the role/collection and adds it as an
    HTML comment at the top of the rendered content.

    Attributes:
        include_metadata: Whether to include metadata in output
    """

    def __init__(self, include_metadata: bool = True):
        """Initialize processor.

        Args:
            include_metadata: Whether to add metadata to content (default: True)
        """
        self.include_metadata = include_metadata

    def add_metadata(self, content: str, role_path: Path) -> str:
        """Add metadata comment to content.

        Generates metadata from the role path and prepends it as an HTML
        comment to the content. If metadata generation fails, logs a warning
        and returns the original content unchanged.

        Args:
            content: The rendered content to add metadata to
            role_path: Path to the role/collection directory

        Returns:
            Content with metadata prepended, or original content if generation fails

        Example:
            >>> processor = MetadataProcessor()
            >>> content_with_metadata = processor.add_metadata(content, Path('/path/to/role'))
        """
        if not self.include_metadata:
            return content

        try:
            metadata = generate_metadata(role_path.resolve())
            return metadata.to_comment() + "\n" + content
        except Exception as e:
            # Don't fail if metadata generation fails
            logger.warning(f"Could not generate metadata: {e}")
            return content
