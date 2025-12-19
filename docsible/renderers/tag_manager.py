"""Tag management for Docsible-generated content in README files."""

import logging
import re
from pathlib import Path

from docsible import constants

logger = logging.getLogger(__name__)


def manage_docsible_tags(content: str) -> str:
    """Add Docsible tags to content if not already present.

    Wraps content in DOCSIBLE_START_TAG and DOCSIBLE_END_TAG to mark
    auto-generated sections.

    Args:
        content: Content to wrap with tags

    Returns:
        Content with Docsible tags

    Example:
        >>> content = "# Role Documentation\\n..."
        >>> tagged = manage_docsible_tags(content)
        >>> "<!-- DOCSIBLE START -->" in tagged
        True
    """
    if constants.DOCSIBLE_START_TAG not in content:
        content = f"{constants.DOCSIBLE_START_TAG}\n{content}"
    if constants.DOCSIBLE_END_TAG not in content:
        content = f"{content}\n{constants.DOCSIBLE_END_TAG}"
    return content


def replace_between_tags(existing_content: str, new_content: str) -> str:
    """Replace content between Docsible tags while preserving manual sections.

    Args:
        existing_content: Existing README content
        new_content: New generated content

    Returns:
        Updated content with replaced auto-generated section

    Example:
        >>> existing = "Manual\\n<!-- DOCSIBLE START -->\\nOld\\n<!-- DOCSIBLE END -->"
        >>> new = "New generated"
        >>> result = replace_between_tags(existing, new)
        >>> "New generated" in result
        True
    """
    pattern = re.compile(
        rf"{re.escape(constants.DOCSIBLE_START_TAG)}.*?{re.escape(constants.DOCSIBLE_END_TAG)}",
        re.DOTALL,
    )
    return pattern.sub(new_content, existing_content)


def manage_docsible_file_keys(docsible_path: Path) -> dict:
    """Load or initialize .docsible metadata file.

    Args:
        docsible_path: Path to .docsible file

    Returns:
        Dictionary with docsible metadata

    Example:
        >>> from pathlib import Path
        >>> data = manage_docsible_file_keys(Path('.docsible'))
        >>> 'description' in data
        True
    """
    import yaml

    default_keys = {
        "description": "",
        "requester": "",
        "users": "",
        "dt_dev": "",
        "dt_prod": "",
        "dt_update": "",
        "version": "",
        "time_saving": "",
        "category": "",
        "subCategory": "",
        "aap_hub": "",
        "automation_kind": "",
        "critical": "",
    }

    if docsible_path.exists():
        try:
            with open(docsible_path, encoding="utf-8") as f:
                existing_data = yaml.safe_load(f) or {}

            # Check if any new keys need to be added
            updated = False
            for key in default_keys:
                if key not in existing_data:
                    existing_data[key] = default_keys[key]
                    updated = True

            if updated:
                with open(docsible_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        existing_data, f, default_flow_style=False, allow_unicode=True
                    )
                logger.info(f"Updated {docsible_path} with new keys.")

            return existing_data

        except Exception as e:
            logger.error(f"Error reading {docsible_path}: {e}")
            return default_keys
    else:
        # Initialize new file
        with open(docsible_path, "w", encoding="utf-8") as f:
            yaml.dump(default_keys, f, default_flow_style=False, allow_unicode=True)
        logger.info(f"Initialized {docsible_path} with default keys.")
        return default_keys
