"""Handles content merging strategies."""

import logging
from pathlib import Path

from docsible import constants
from docsible.renderers.tag_manager import replace_between_tags

logger = logging.getLogger(__name__)


class ContentMerger:
    """Merges new content with existing files."""
    
    def merge(
        self, 
        output_path: Path, 
        new_content: str, 
        append: bool
    ) -> str:
        """Merge new content with existing file based on append mode.
        
        Args:
            output_path: Path to output file
            new_content: New generated content
            append: Whether to append or replace
            
        Returns:
            Final merged content
        """
        if not output_path.exists():
            return new_content
        
        with open(output_path, encoding="utf-8") as f:
            existing_content = f.read()
        
        if not append:
            return new_content
        
        # Append mode: replace between tags or append to end
        if (
            constants.DOCSIBLE_START_TAG in existing_content
            and constants.DOCSIBLE_END_TAG in existing_content
        ):
            return replace_between_tags(existing_content, new_content)
        else:
            return f"{existing_content}\n{new_content}"
