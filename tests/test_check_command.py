from docsible.utils.metadata import generate_metadata
from docsible.commands.check.core import check_documentation_drift


def test_check_fresh_documentation(tmp_path):
    """Test checking fresh documentation."""
    # Create role
    role_path = tmp_path / "role"
    role_path.mkdir()
    (role_path / "defaults").mkdir()
    (role_path / "defaults/main.yml").write_text("foo: bar")
    
    # Generate metadata
    metadata = generate_metadata(role_path)
    
    # Create README with metadata
    readme = role_path / "README.md"
    readme.write_text(metadata.to_comment() + "\n# My Role")
    
    # Check should pass
    is_fresh, details = check_documentation_drift(role_path, readme)
    
    assert is_fresh is True


def test_check_outdated_documentation(tmp_path):
    """Test checking outdated documentation."""
    # Create role
    role_path = tmp_path / "role"
    role_path.mkdir()
    (role_path / "defaults").mkdir()
    (role_path / "defaults/main.yml").write_text("foo: bar")
    
    # Generate metadata
    metadata = generate_metadata(role_path)
    
    # Create README
    readme = role_path / "README.md"
    readme.write_text(metadata.to_comment() + "\n# My Role")
    
    # Modify role file
    (role_path / "defaults/main.yml").write_text("foo: changed")
    
    # Check should fail
    is_fresh, details = check_documentation_drift(role_path, readme)
    
    assert is_fresh is False
    assert "changed" in details['reason'].lower()
