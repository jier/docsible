from docsible.utils.metadata import GenerationMetadata, generate_metadata
from datetime import datetime
from docsible.constants import VERSION

def test_generate_metadata(tmp_path):
    """Test metadata generation."""
    # Create fake role
    (tmp_path / "defaults").mkdir()
    (tmp_path / "defaults/main.yml").write_text("foo: bar")
    
    metadata = generate_metadata(tmp_path)
    
    assert metadata.docsible_version == VERSION
    assert len(metadata.role_hash) == 16
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