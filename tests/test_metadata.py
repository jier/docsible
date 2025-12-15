from docsible.utils.metadata import GenerationMetadata, generate_metadata, compute_role_hash
from datetime import datetime, timezone
from docsible.constants import VERSION
import pytest
from pydantic import ValidationError



def test_metadata_validation():
    """Test Pydantic validation."""
    # Valid metadata
    metadata = GenerationMetadata(
        generated_at=datetime.now(tz=timezone.utc),
        docsible_version="0.8.0",
        role_hash="355a0d9667b6450491caf06c768be06a0a1e56b615bf9c7bef07b27c2c792704"
    )
    assert metadata.role_hash == "355a0d9667b6450491caf06c768be06a0a1e56b615bf9c7bef07b27c2c792704"
    
    # Invalid hash length
    with pytest.raises(ValidationError, match="String should have at least 64 characters"):
        GenerationMetadata(
            generated_at=datetime.now(tz=timezone.utc),
            docsible_version="0.8.0",
            role_hash="abc1234"  # Too short
        )
    # Invalid hash length - too long
    with pytest.raises(ValidationError, match="role_hash must be 64 hex characters"):
        GenerationMetadata(
            generated_at=datetime.utcnow(),
            docsible_version="0.8.0",
            role_hash="a" * 65  # Too long
        )


def test_generate_metadata(tmp_path):
    """Test metadata generation."""
    # Create fake role
    (tmp_path / "defaults").mkdir()
    (tmp_path / "defaults/main.yml").write_text("foo: bar")
    
    metadata = generate_metadata(tmp_path)
    # Type checks (Pydantic guarantees types)
    assert isinstance(metadata.generated_at, datetime)
    assert isinstance(metadata.docsible_version, str)
    assert isinstance(metadata.role_hash, str)

    assert metadata.docsible_version == VERSION
    assert len(metadata.role_hash) == 64
    assert metadata.generated_at is not None


def test_metadata_to_comment():
    """Test converting metadata to HTML comment."""
    metadata = GenerationMetadata(
        generated_at=datetime(2025, 12, 15, 10, 30, 0),
        docsible_version="0.8.0",
        role_hash="355a0d9667b6450491caf06c768be06a0a1e56b615bf9c7bef07b27c2c792704"
    )
    
    comment = metadata.to_comment()
    
    assert "<!-- DOCSIBLE METADATA" in comment
    assert "2025-12-15T10:30:00Z" in comment
    assert "0.8.0" in comment
    assert "355a0d9667b6450491caf06c768be" in comment


def test_metadata_from_comment():
    """Test parsing metadata from comment."""
    markdown = """<!-- DOCSIBLE METADATA
generated_at: 2025-12-15T10:30:00Z
docsible_version: 0.8.0
role_hash: 355a0d9667b6450491caf06c768be06a0a1e56b615bf9c7bef07b27c2c792704
-->
# My Role
"""
    
    metadata = GenerationMetadata.from_comment(markdown)
    
    assert metadata is not None
    assert metadata.docsible_version == "0.8.0"
    assert metadata.role_hash == "355a0d9667b6450491caf06c768be06a0a1e56b615bf9c7bef07b27c2c792704"

def test_metadata_from_invalid_comment():
    """Test parsing invalid metadata returns None."""
    # No metadata
    assert GenerationMetadata.from_comment("# Just a README") is None
    
    # Malformed metadata
    bad_markdown = """<!-- DOCSIBLE METADATA
    generated_at: not-a-date
    -->"""
    assert GenerationMetadata.from_comment(bad_markdown) is None


def test_compute_role_hash(tmp_path):
    """Test computing role hash."""
    # Create role files
    (tmp_path / "defaults").mkdir()
    (tmp_path / "defaults/main.yml").write_text("var1: value1")
    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks/main.yml").write_text("- name: Task 1")
    
    hash1 = compute_role_hash(tmp_path)
    
    # Hash should be 16 hex characters
    assert len(hash1) == 64
    assert all(c in '0123456789abcdef' for c in hash1)
    
    # Same files = same hash (deterministic)
    hash2 = compute_role_hash(tmp_path)
    assert hash1 == hash2
    
    # Change file = different hash
    (tmp_path / "defaults/main.yml").write_text("var1: changed")
    hash3 = compute_role_hash(tmp_path)
    assert hash1 != hash3


def test_json_serialization():
    """Test Pydantic JSON serialization."""
    metadata = GenerationMetadata(
        generated_at=datetime(2025, 12, 15, 10, 30, 0),
        docsible_version="0.8.0",
        role_hash="355a0d9667b6450491caf06c768be06a0a1e56b615bf9c7bef07b27c2c792704"
    )
    
    # Serialize to JSON
    json_str = metadata.model_dump_json()
    assert "2025-12-15T10:30:00Z" in json_str
    assert "0.8.0" in json_str
    
    # Deserialize from JSON
    loaded = GenerationMetadata.model_validate_json(json_str)
    assert loaded.docsible_version == metadata.docsible_version
    assert loaded.role_hash == metadata.role_hash