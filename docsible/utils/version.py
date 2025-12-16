"""Dynamic version detection using git tags with fallback to constants."""

import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def get_git_version() -> Optional[str]:
    """Get version from git tags.

    Returns version in format:
    - "X.Y.Z" if on a tagged commit
    - "X.Y.Z.devN+gHHHHHHH" if N commits after tag X.Y.Z
    - None if not in a git repository or no tags found

    Examples:
        On tag v0.8.0:       returns "0.8.0"
        5 commits after tag: returns "0.8.0.dev5+gabc1234"

    Returns:
        Version string or None
    """
    try:
        # Check if we're in a git repository
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )
        if result.returncode != 0:
            return None

        # Get the version from git describe
        result = subprocess.run(
            ["git", "describe", "--tags", "--long", "--abbrev=7", "--match=v*"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )

        if result.returncode != 0:
            # No tags found
            return None

        # Parse output: "v0.8.0-5-gabc1234" -> "0.8.0.dev5+gabc1234"
        git_describe = result.stdout.strip()

        # Extract components: tag-commits-hash
        parts = git_describe.split("-")
        if len(parts) < 3:
            return None

        # Remove 'v' prefix from tag
        tag = parts[0].lstrip("v")
        commits_since_tag = int(parts[1])
        commit_hash = parts[2]  # Already has 'g' prefix

        if commits_since_tag == 0:
            # On a tagged commit
            return tag
        else:
            # Development version
            return f"{tag}.dev{commits_since_tag}+{commit_hash}"

    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
        logger.debug(f"Could not get git version: {e}")
        return None
    except Exception as e:
        logger.debug(f"Unexpected error getting git version: {e}")
        return None


def get_version() -> str:
    """Get the application version.

    Tries git tags first, falls back to constants.VERSION.

    Returns:
        Version string (e.g., "0.8.0" or "0.8.0.dev5+gabc1234")
    """
    # Try git version first
    git_version = get_git_version()
    if git_version:
        return git_version

    # Fall back to constants
    from docsible.constants import VERSION
    return VERSION


def get_version_info() -> dict:
    """Get detailed version information.

    Returns:
        Dictionary with keys:
        - version: str (e.g., "0.8.0" or "0.8.0.dev5+gabc1234")
        - source: str ("git" or "constants")
        - is_dev: bool (True if development version)
    """
    git_version = get_git_version()

    if git_version:
        is_dev = ".dev" in git_version
        return {
            "version": git_version,
            "source": "git",
            "is_dev": is_dev,
        }
    else:
        from docsible.constants import VERSION
        return {
            "version": VERSION,
            "source": "constants",
            "is_dev": False,
        }
