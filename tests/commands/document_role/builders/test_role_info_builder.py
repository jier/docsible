"""Tests for RoleInfoBuilder class."""

import tempfile
from pathlib import Path

import pytest
import yaml

from docsible.commands.document_role.builders.role_info_builder import RoleInfoBuilder
from docsible.commands.document_role.models import ProcessingConfig, RepositoryConfig
from docsible.utils.project_structure import ProjectStructure


class TestRoleInfoBuilder:
    """Test RoleInfoBuilder class."""

    @pytest.fixture
    def temp_role_dir(self):
        """Create a temporary role directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            role_path = Path(tmpdir) / "test_role"
            role_path.mkdir()

            # Create standard role directories
            (role_path / "defaults").mkdir()
            (role_path / "vars").mkdir()
            (role_path / "tasks").mkdir()
            (role_path / "handlers").mkdir()
            (role_path / "meta").mkdir()

            # Create basic meta/main.yml
            meta_content = {
                "galaxy_info": {
                    "author": "Test Author",
                    "description": "Test role",
                    "license": "MIT",
                },
                "dependencies": [],
            }
            with open(role_path / "meta" / "main.yml", "w") as f:
                yaml.dump(meta_content, f)

            # Create defaults/main.yml
            defaults_content = {"test_var": "default_value", "test_number": 42}
            with open(role_path / "defaults" / "main.yml", "w") as f:
                yaml.dump(defaults_content, f)

            # Create vars/main.yml
            vars_content = {"test_var_override": "vars_value"}
            with open(role_path / "vars" / "main.yml", "w") as f:
                yaml.dump(vars_content, f)

            # Create tasks/main.yml
            tasks_content = [
                {"name": "Install package", "apt": {"name": "nginx", "state": "present"}},
                {"name": "Start service", "service": {"name": "nginx", "state": "started"}},
            ]
            with open(role_path / "tasks" / "main.yml", "w") as f:
                yaml.dump(tasks_content, f)

            # Create handlers/main.yml
            handlers_content = [
                {"name": "Restart nginx", "service": {"name": "nginx", "state": "restarted"}},
            ]
            with open(role_path / "handlers" / "main.yml", "w") as f:
                yaml.dump(handlers_content, f)

            yield role_path

    def test_basic_role_info_building(self, temp_role_dir):
        """Test basic role information building."""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["name"] == "test_role"
        assert "meta" in role_info
        assert "defaults" in role_info
        assert "vars" in role_info
        assert "tasks" in role_info
        assert "handlers" in role_info
        assert "playbook" in role_info

    def test_meta_info_extraction(self, temp_role_dir):
        """Test metadata extraction."""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["meta"]["galaxy_info"]["author"] == "Test Author"
        assert role_info["meta"]["galaxy_info"]["description"] == "Test role"
        assert role_info["meta"]["galaxy_info"]["license"] == "MIT"

    def test_vars_info_extraction(self, temp_role_dir):
        """Test defaults and vars extraction."""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        # Check defaults - load_yaml_files_from_dir_custom returns list with structure:
        # [{"file": "filename", "data": {...}}, ...]
        assert len(role_info["defaults"]) > 0

        # Check for the presence of our test variables in the data
        found_test_var = False
        found_test_number = False
        for defaults_entry in role_info["defaults"]:
            if "data" in defaults_entry:
                data = defaults_entry["data"]
                # data has structure like: {"key_name": {"value": actual_value, "metadata": ...}}
                for key, value_info in data.items():
                    if key == "test_var" and value_info.get("value") == "default_value":
                        found_test_var = True
                    if key == "test_number" and value_info.get("value") == 42:
                        found_test_number = True
        assert found_test_var
        assert found_test_number

        # Check vars
        assert len(role_info["vars"]) > 0
        found_test_var_override = False
        for vars_entry in role_info["vars"]:
            if "data" in vars_entry:
                data = vars_entry["data"]
                for key, value_info in data.items():
                    if key == "test_var_override" and value_info.get("value") == "vars_value":
                        found_test_var_override = True
        assert found_test_var_override

    def test_tasks_info_extraction(self, temp_role_dir):
        """Test task extraction."""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert len(role_info["tasks"]) == 1
        task_file = role_info["tasks"][0]
        assert task_file["file"] == "main.yml"
        assert len(task_file["tasks"]) == 2
        assert task_file["tasks"][0]["name"] == "Install package"
        assert task_file["tasks"][1]["name"] == "Start service"

    def test_tasks_with_comments(self, temp_role_dir):
        """Test task extraction with comments enabled."""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig(comments=True)
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        task_file = role_info["tasks"][0]
        assert "comments" in task_file
        assert isinstance(task_file["comments"], list)

    def test_tasks_with_line_numbers(self, temp_role_dir):
        """Test task extraction with line numbers enabled."""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig(task_line=True)
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        task_file = role_info["tasks"][0]
        assert "lines" in task_file
        # get_task_line_numbers returns a dict mapping task names to line numbers
        assert isinstance(task_file["lines"], dict)

    def test_handlers_info_extraction(self, temp_role_dir):
        """Test handler extraction."""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert len(role_info["handlers"]) == 1
        handler = role_info["handlers"][0]
        assert handler["name"] == "Restart nginx"
        assert handler["module"] == "service"
        assert handler["file"] == "main.yml"

    def test_playbook_info_without_content(self, temp_role_dir):
        """Test playbook info when no playbook provided."""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["playbook"]["content"] is None
        assert role_info["playbook"]["graph"] is None
        assert role_info["playbook"]["dependencies"] == []

    def test_playbook_info_with_content(self, temp_role_dir):
        """Test playbook info extraction with playbook content."""
        playbook_content = """
- name: Test playbook
  hosts: all
  roles:
    - test_role
    - other_role
"""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=playbook_content,
            processing=processing,
            repository=repository,
        )

        assert role_info["playbook"]["content"] == playbook_content
        assert "other_role" in role_info["playbook"]["dependencies"]
        assert "test_role" not in role_info["playbook"]["dependencies"]

    def test_playbook_dependencies_extraction(self, temp_role_dir):
        """Test playbook dependency extraction."""
        playbook_content = """
- name: Test playbook
  hosts: all
  roles:
    - role: dep_role_1
    - { role: dep_role_2, var: value }
  tasks:
    - include_role:
        name: dep_role_3
    - import_role:
        name: dep_role_4
"""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=playbook_content,
            processing=processing,
            repository=repository,
        )

        dependencies = role_info["playbook"]["dependencies"]
        assert "dep_role_1" in dependencies
        assert "dep_role_2" in dependencies
        assert "dep_role_3" in dependencies
        assert "dep_role_4" in dependencies
        assert len(dependencies) == 4

    def test_repository_info_no_url(self, temp_role_dir):
        """Test repository info when no URL provided."""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["repository"] is None
        assert role_info["repository_type"] is None
        assert role_info["repository_branch"] is None

    def test_repository_info_with_url(self, temp_role_dir):
        """Test repository info with provided URL."""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig(
            repository_url="https://github.com/user/repo",
            repo_type="github",
            repo_branch="main",
        )

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["repository"] == "https://github.com/user/repo"
        assert role_info["repository_type"] == "github"
        assert role_info["repository_branch"] == "main"

    def test_missing_meta_directory(self, temp_role_dir):
        """Test behavior when meta directory is missing."""
        # Remove meta directory
        import shutil

        shutil.rmtree(temp_role_dir / "meta")

        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["meta"] == {}

    def test_missing_tasks_directory(self, temp_role_dir):
        """Test behavior when tasks directory is missing."""
        import shutil

        shutil.rmtree(temp_role_dir / "tasks")

        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["tasks"] == []

    def test_missing_handlers_directory(self, temp_role_dir):
        """Test behavior when handlers directory is missing."""
        import shutil

        shutil.rmtree(temp_role_dir / "handlers")

        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["handlers"] == []

    def test_belongs_to_collection(self, temp_role_dir):
        """Test collection info is included."""
        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()
        collection_info = {"namespace": "my_namespace", "name": "my_collection"}

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
            belongs_to_collection=collection_info,
        )

        assert role_info["belongs_to_collection"] == collection_info
        assert role_info["belongs_to_collection"]["namespace"] == "my_namespace"

    def test_argument_specs(self, temp_role_dir):
        """Test argument specs extraction."""
        # Create argument specs file
        argument_specs_path = temp_role_dir / "meta" / "argument_specs.yml"
        argument_specs_content = {
            "argument_specs": {
                "main": {
                    "short_description": "Main entry point",
                    "options": {
                        "test_option": {
                            "type": "str",
                            "required": True,
                            "description": "Test option",
                        }
                    },
                }
            }
        }
        with open(argument_specs_path, "w") as f:
            yaml.dump(argument_specs_content, f)

        builder = RoleInfoBuilder()
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["argument_specs"] is not None
        assert "argument_specs" in role_info["argument_specs"]

    def test_no_docsible_flag(self, temp_role_dir):
        """Test that no_docsible flag is respected."""
        # Create .docsible file
        docsible_path = temp_role_dir / ".docsible"
        docsible_content = {"custom_key": "custom_value"}
        with open(docsible_path, "w") as f:
            yaml.dump(docsible_content, f)

        builder = RoleInfoBuilder()
        processing = ProcessingConfig(no_docsible=True)
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["docsible"] is None

    def test_with_docsible_file(self, temp_role_dir):
        """Test docsible file is loaded when no_docsible is False."""
        # Create .docsible file
        docsible_path = temp_role_dir / ".docsible"
        docsible_content = {"custom_key": "custom_value"}
        with open(docsible_path, "w") as f:
            yaml.dump(docsible_content, f)

        builder = RoleInfoBuilder()
        processing = ProcessingConfig(no_docsible=False)
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["docsible"] is not None
        assert role_info["docsible"]["custom_key"] == "custom_value"

    def test_project_structure_injection(self, temp_role_dir):
        """Test that project_structure can be injected."""
        project_structure = ProjectStructure(str(temp_role_dir))
        builder = RoleInfoBuilder(project_structure=project_structure)
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["name"] == "test_role"
        assert builder.project_structure is project_structure

    def test_project_structure_auto_creation(self, temp_role_dir):
        """Test that project_structure is auto-created if not provided."""
        builder = RoleInfoBuilder(project_structure=None)
        processing = ProcessingConfig()
        repository = RepositoryConfig()

        assert builder.project_structure is None

        role_info = builder.build(
            role_path=temp_role_dir,
            playbook_content=None,
            processing=processing,
            repository=repository,
        )

        assert role_info["name"] == "test_role"
        assert builder.project_structure is not None
