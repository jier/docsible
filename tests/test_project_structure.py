"""
Test suite for ProjectStructure class
"""
import os
import tempfile
import shutil
from pathlib import Path
from docsible.utils.project_structure import ProjectStructure


def test_standard_role_detection():
    """Test that a standard role structure is detected correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create standard role structure
        role_path = Path(tmpdir)
        (role_path / 'tasks').mkdir()
        (role_path / 'defaults').mkdir()
        (role_path / 'vars').mkdir()
        (role_path / 'meta').mkdir()

        project = ProjectStructure(str(role_path))

        assert project.project_type == 'role', f"Expected 'role', got '{project.project_type}'"
        assert project.get_defaults_dir().name == 'defaults'
        assert project.get_vars_dir().name == 'vars'
        assert project.get_tasks_dir().name == 'tasks'
        assert project.get_meta_dir().name == 'meta'

    print("✓ Standard role detection test passed")


def test_collection_detection():
    """Test that a collection structure is detected correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create collection structure
        collection_path = Path(tmpdir)
        (collection_path / 'galaxy.yml').touch()
        (collection_path / 'roles').mkdir()

        project = ProjectStructure(str(collection_path))

        assert project.project_type == 'collection', f"Expected 'collection', got '{project.project_type}'"
        assert project.get_roles_dir().name == 'roles'

    print("✓ Collection detection test passed")


def test_monorepo_detection():
    """Test that a monorepo structure is detected correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create monorepo structure
        monorepo_path = Path(tmpdir)
        (monorepo_path / 'ansible' / 'roles').mkdir(parents=True)

        project = ProjectStructure(str(monorepo_path))

        assert project.project_type == 'monorepo', f"Expected 'monorepo', got '{project.project_type}'"
        roles_dir = project.get_roles_dir()
        assert 'ansible' in str(roles_dir) and 'roles' in str(roles_dir)

    print("✓ Monorepo detection test passed")


def test_multi_role_detection():
    """Test that a regular repo with just roles/ folder is detected correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multi-role structure (no galaxy.yml, just roles/)
        multi_role_path = Path(tmpdir)
        roles_dir = multi_role_path / 'roles'
        roles_dir.mkdir()

        # Create a couple of roles
        (roles_dir / 'role1' / 'tasks').mkdir(parents=True)
        (roles_dir / 'role2' / 'tasks').mkdir(parents=True)

        project = ProjectStructure(str(multi_role_path))

        assert project.project_type == 'multi-role', f"Expected 'multi-role', got '{project.project_type}'"
        assert project.get_roles_dir().name == 'roles'

        # Test that find_roles works
        roles = project.find_roles()
        assert len(roles) == 2, f"Expected 2 roles, found {len(roles)}"

    print("✓ Multi-role detection test passed")


def test_awx_detection():
    """Test that AWX project structure is detected correctly (requires BOTH roles/ and inventory/)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create AWX structure with BOTH roles/ and inventory/
        awx_path = Path(tmpdir)
        (awx_path / 'roles').mkdir()
        (awx_path / 'inventory').mkdir()

        project = ProjectStructure(str(awx_path))

        assert project.project_type == 'awx', f"Expected 'awx', got '{project.project_type}'"

    # Test that just roles/ alone is NOT detected as AWX
    with tempfile.TemporaryDirectory() as tmpdir:
        just_roles_path = Path(tmpdir)
        (just_roles_path / 'roles').mkdir()

        project = ProjectStructure(str(just_roles_path))

        assert project.project_type != 'awx', f"Expected NOT 'awx', got '{project.project_type}'"
        assert project.project_type == 'multi-role', f"Expected 'multi-role', got '{project.project_type}'"

    print("✓ AWX detection test passed")


def test_custom_config():
    """Test that custom configuration from .docsible.yml is loaded"""
    with tempfile.TemporaryDirectory() as tmpdir:
        role_path = Path(tmpdir)
        (role_path / 'tasks').mkdir()

        # Create custom config
        config_content = """structure:
  defaults_dir: 'custom_defaults'
  vars_dir: 'custom_vars'
  tasks_dir: 'custom_tasks'
"""
        with open(role_path / '.docsible.yml', 'w') as f:
            f.write(config_content)

        project = ProjectStructure(str(role_path))

        assert project.get_defaults_dir().name == 'custom_defaults'
        assert project.get_vars_dir().name == 'custom_vars'
        assert project.get_tasks_dir().name == 'custom_tasks'

    print("✓ Custom configuration test passed")


def test_yaml_extensions():
    """Test that YAML extensions are properly configured"""
    with tempfile.TemporaryDirectory() as tmpdir:
        role_path = Path(tmpdir)
        (role_path / 'tasks').mkdir()

        project = ProjectStructure(str(role_path))

        extensions = project.get_yaml_extensions()
        assert '.yml' in extensions
        assert '.yaml' in extensions

    print("✓ YAML extensions test passed")


def test_meta_file_discovery():
    """Test that meta files are discovered with both .yml and .yaml extensions"""
    with tempfile.TemporaryDirectory() as tmpdir:
        role_path = Path(tmpdir)
        meta_dir = role_path / 'meta'
        meta_dir.mkdir()

        # Test with .yml
        (meta_dir / 'main.yml').touch()
        project = ProjectStructure(str(role_path))
        meta_file = project.get_meta_file()
        assert meta_file is not None
        assert meta_file.name == 'main.yml'

    with tempfile.TemporaryDirectory() as tmpdir:
        role_path = Path(tmpdir)
        meta_dir = role_path / 'meta'
        meta_dir.mkdir()

        # Test with .yaml
        (meta_dir / 'main.yaml').touch()
        project = ProjectStructure(str(role_path))
        meta_file = project.get_meta_file()
        assert meta_file is not None
        assert meta_file.name == 'main.yaml'

    print("✓ Meta file discovery test passed")


def test_backward_compatibility():
    """Test that default paths match the original hardcoded values"""
    with tempfile.TemporaryDirectory() as tmpdir:
        role_path = Path(tmpdir)
        (role_path / 'tasks').mkdir()

        project = ProjectStructure(str(role_path))

        # These should match the original hardcoded paths
        assert str(project.get_defaults_dir(role_path)).endswith('defaults')
        assert str(project.get_vars_dir(role_path)).endswith('vars')
        assert str(project.get_tasks_dir(role_path)).endswith('tasks')
        assert str(project.get_meta_dir(role_path)).endswith('meta')

    print("✓ Backward compatibility test passed")


if __name__ == '__main__':
    print("Running ProjectStructure tests...\n")

    try:
        test_standard_role_detection()
        test_collection_detection()
        test_monorepo_detection()
        test_multi_role_detection()
        test_awx_detection()
        test_custom_config()
        test_yaml_extensions()
        test_meta_file_discovery()
        test_backward_compatibility()

        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
