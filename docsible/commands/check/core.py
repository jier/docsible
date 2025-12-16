"""Check logic to detect README content drift compared to last generated"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

from docsible.utils.metadata import GenerationMetadata, compute_role_hash


def check_documentation_drift(role_path: Path, readme_path: Path) -> Tuple[bool, Dict]:
    """
    Check if documentation is up to date.

    Args:
        role_path: Path to role directory
        readme_path: Path to README file

    Returns:
        Tuple of (is_fresh, details_dict)
    """
    # Check if README exists
    if not readme_path.exists():
        return False, {
            "reason": "README.md not found",
            "recommendation": "Run: docsible role --role .",
        }

    # Parse metadata from README
    readme_content = readme_path.read_text()
    metadata = GenerationMetadata.from_comment(readme_content)

    if not metadata:
        return False, {
            "reason": "README.md does not contain docsible metadata (may be manually created)",
            "recommendation": "Run: docsible role --role . --no-backup",
        }

    # Compute current hash
    current_hash = compute_role_hash(role_path)

    # Check if role files changed
    if metadata.role_hash != current_hash:
        changed_files = _find_changed_files(role_path, metadata.generated_at)
        return False, {
            "reason": "Role files have changed since documentation was generated",
            "changed_files": changed_files,
            "generated_at": metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "recommendation": "Run: docsible role --role . --no-backup",
        }

    # Documentation is fresh!
    return True, {
        "generated_at": metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "docsible_version": metadata.docsible_version,
    }


def _find_changed_files(role_path: Path, since: datetime) -> list:
    """Find files modified since given timestamp."""
    changed = []

    patterns = [
        "defaults/**/*.yml",
        "defaults/**/*.yaml",
        "vars/**/*.yml",
        "vars/**/*.yaml",
        "tasks/**/*.yml",
        "tasks/**/*.yaml",
        "handlers/**/*.yml",
        "handlers/**/*.yaml",
        "meta/main.yml",
        "meta/main.yaml",
    ]

    for pattern in patterns:
        for file_path in role_path.glob(pattern):
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime).replace(
                    tzinfo=timezone.utc
                )
                if mtime > since:
                    changed.append(str(file_path.relative_to(role_path)))

    return changed
