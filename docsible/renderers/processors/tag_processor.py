import logging

from docsible.renderers.tag_manager import manage_docsible_tags

logger = logging.getLogger(__name__)


class TagProcessor:
    """Manages Docsible tags in content.

    Wraps generated content with Docsible start/end tags to mark
    sections that are auto-generated and should be managed by Docsible.
    """

    def add_tags(self, content: str) -> str:
        """Add Docsible start/end tags to content.

        Wraps the content with special comment tags that mark the boundaries
        of Docsible-managed content. This allows for safe updates without
        overwriting manually edited sections.

        Args:
            content: The rendered content to wrap with tags

        Returns:
            Content wrapped with Docsible tags

        Example:
            >>> processor = TagProcessor()
            >>> tagged = processor.add_tags("# My Role\\n\\nContent here")
            >>> print(tagged)
            <!-- DOCSIBLE_START -->
            # My Role

            Content here
            <!-- DOCSIBLE_END -->
        """
        return manage_docsible_tags(content)
