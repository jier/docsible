import datetime as dt
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_serializer, field_validator

from docsible.constants import VERSION

"Track when README becomes outdated when role files changes."

"Exit code 0 (up-to-date) or 1 (outdated)."
" And show what has changed and when"


class GenerationMetadata(BaseModel):
    """
    Metadata about document generation.

    Tracks when documentation was generated and the state of the role files
    to enable drift detection.

    Attributes:
        generated_at: UTC timestamp when documentation was generated
        docsible_version: Version of Docsible used for generation
        role_hash: SHA256 hash of all role YAML files (64 chars)
    """

    generated_at: datetime = Field(
        description="UTC timestamp when documentation was generated"
    )
    docsible_version: str = Field(description="Version of Docsible used for generation")
    role_hash: str = Field(
        description="SHA256 hash of role files (64 characters)",
        min_length=64,
    )

    @field_validator("role_hash")
    @classmethod
    def validate_hash(cls, hash: str) -> str:
        """
        Ensure hash  is valid hexadecimal.

        :param hash: to validate hash
        :type hash: str
        :return: hash
        :rtype: str
        """
        if not re.match(r"^[0-f0-9]{64}$", hash):
            raise ValueError("role_hash must be 64 hex characters long")
        return hash

    @field_serializer("generated_at")
    def serialize_datetime(self, dt: datetime, _info) -> str:
        """
        Serialize datetime to ISO format with 'Z' timezone indicator.

        This ensures JSON serialization includes the 'Z' suffix for UTC times,
        matching the format expected by from_comment() and maintaining consistency.

        :param dt: datetime to serialize
        :type dt: datetime
        :return: ISO format string with 'Z' suffix
        :rtype: str
        """
        return dt.isoformat() + "Z"

    def to_comment(self) -> str:
        """
        Convert metadata to HTML comment for README.

        Returns:
            HTML comment block with metadata that can be embedded in README

        Example:
            >>> metadata = GenerationMetadata(...)
            >>> comment = metadata.to_comment()
            >>> print(comment)
            <!-- DOCSIBLE METADATA
            generated_at: 2025-12-15T10:30:00Z
            docsible_version: 0.8.0
            role_hash: "355a0d9667b6450491caf06c768be06a0a1e56b615bf9c7bef07b27c2c792704"
            -->
        """
        return f"""<!-- DOCSIBLE METADATA
generated_at: {self.generated_at.isoformat()}Z
docsible_version: {self.docsible_version}
role_hash: {self.role_hash}
-->"""

    @classmethod
    def from_comment(cls, markdown: str) -> Optional["GenerationMetadata"]:
        """
        Parse metadata from README HTML comment.

        Args:
            markdown: README content that may contain metadata comment

        Returns:
            GenerationMetadata if found and valid, None otherwise

        Example:
            >>> readme = Path('README.md').read_text()
            >>> metadata = GenerationMetadata.from_comment(readme)
            >>> if metadata:
            ...     print(f"Generated at: {metadata.generated_at}")
        """
        pattern = r"<!-- DOCSIBLE METADATA\ngenerated_at: (.+)\ndocsible_version: (.+)\nrole_hash: (.+)\n-->"
        match = re.search(pattern, markdown)

        if not match:
            return None

        try:
            return cls(
                generated_at=dt.datetime.fromisoformat(match.group(1).rstrip("Z")),
                docsible_version=match.group(2),
                role_hash=match.group(3),
            )
        except Exception:
            # Invalid metadata format - return None
            return None


def compute_role_hash(role_path: Path) -> str:
    """
    Compute hash of all role YAML files to detect changes.

    Scans all YAML files in standard Ansible role directories and computes
    a SHA256 hash. Any change to these files will result in a different hash.

    Args:
        role_path: Path to role directory

    Returns:
        64-character hex hash string

    Raises:
        ValueError: If role_path doesn't exist

    Example:
        >>> role_hash = compute_role_hash(Path('/path/to/role'))
        >>> print(role_hash)
        'abc123def4567890'
    """
    if not role_path.exists():
        raise ValueError(f"Role path does not exist: {role_path}")

    hash_obj = hashlib.sha256()

    # Patterns for role files that affect documentation
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

    # Sort files for consistent hashing across platforms
    from pathlib import Path
    all_files: list[Path] = []
    for pattern in patterns:
        all_files.extend(role_path.glob(pattern))

    # Hash file paths and contents
    for file_path in sorted(all_files):
        if file_path.is_file():
            # Include relative path in hash (detects renames)
            relative_path = str(file_path.relative_to(role_path))
            hash_obj.update(relative_path.encode("utf-8"))

            # Include file contents
            hash_obj.update(file_path.read_bytes())

    return hash_obj.hexdigest()


def generate_metadata(role_path: Path) -> GenerationMetadata:
    """
    Generate metadata for current documentation generation.

    Args:
        role_path: Path to role directory

    Returns:
        GenerationMetadata with current timestamp, version, and role hash

    Example:
        >>> metadata = generate_metadata(Path('./my-role'))
        >>> print(metadata.docsible_version)
        '0.8.0'
    """
    return GenerationMetadata(
        generated_at=datetime.now(tz=timezone.utc),
        docsible_version=VERSION,
        role_hash=compute_role_hash(role_path),
    )
