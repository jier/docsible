"""
Test cases for docsible-init-config command.
"""

from pathlib import Path
import pytest
import yaml
from click.testing import CliRunner

from docsible.cli import init_config


@pytest.fixture
def config_examples_path() -> Path:
    """Path to config examples."""
    return Path(__file__).parent / "fixtures" / "init_config_examples"


class TestInitConfigCommand:
    """Test the init config command."""

    def test_init_config_creates_file(self, tmp_path):
        """Test that init-config creates .docsible.yml file."""
        runner = CliRunner()
        result = runner.invoke(init_config, ["--path", str(tmp_path)])

        assert result.exit_code == 0, f"Command failed with: {result.output}"
        config_path = tmp_path / ".docsible.yml"
        assert config_path.exists()

    def test_init_config_content(self, tmp_path):
        """Test that init-config creates valid YAML with correct structure."""
        runner = CliRunner()
        # Pass --path explicitly to tell it where to create the file
        result = runner.invoke(init_config, ["--path", str(tmp_path)])

        # Verify command succeeded
        assert result.exit_code == 0

        config_path = tmp_path / ".docsible.yml"
        assert config_path.exists(), "Config file was not created"

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check for standard keys
        assert "defaults_dir" in config["structure"]
        assert "vars_dir" in config["structure"]
        assert "tasks_dir" in config["structure"]
        assert "meta_dir" in config["structure"]
        assert "handlers_dir" in config["structure"]
        assert "yaml_extensions" in config["structure"]
        assert "library_dir" in config["structure"]
        assert "templates_dir" in config["structure"]
        assert "lookup_plugins_dir" in config["structure"]

        # Check default values
        assert config["structure"]["defaults_dir"] == "defaults"
        assert config["structure"]["vars_dir"] == "vars"
        assert config["structure"]["tasks_dir"] == "tasks"
        assert config["structure"]["library_dir"] == "library"
        assert config["structure"]["templates_dir"] == "templates"
        assert config["structure"]["lookup_plugins_dir"] == "lookup_plugins"
        assert ".yml" in config["structure"]["yaml_extensions"]

    def test_init_config_not_overwrite_existing(self, tmp_path):
        """Test that init-config does not overwrite existing config without --force."""
        # Create initial config
        config_path = tmp_path / ".docsible.yml"
        initial_content = {"custom_key": "custom_value"}
        with open(config_path, "w") as f:
            yaml.dump(initial_content, f)

        runner = CliRunner()
        result = runner.invoke(init_config, ["--path", str(tmp_path)])

        # Command should fail when file exists without --force
        assert result.exit_code == 1
        assert "already exists" in result.output.lower()

        # The file should remain unchanged
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Original content should be preserved
        assert "custom_key" in config
        assert config["custom_key"] == "custom_value"

        # Should not have overwritten with default config
        # (if it was overwritten, custom_key would be gone)
        assert config == initial_content


class TestConfigExamples:
    """Test various configuration examples."""

    def test_standard_role_config(self, config_examples_path):
        """Test standard role configuration."""
        config_file = config_examples_path / "standard_role_config.yml"
        assert config_file.exists()

        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config["structure"]["project_type"] == "role"
        assert config["structure"]["defaults_dir"] == "defaults"
        assert config["structure"]["vars_dir"] == "vars"
        assert config["structure"]["tasks_dir"] == "tasks"

    def test_custom_directories_config(self, config_examples_path):
        """Test custom directories configuration."""
        config_file = config_examples_path / "custom_directories_config.yml"
        assert config_file.exists()

        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config["structure"]["project_type"] == "role"
        assert config["structure"]["defaults_dir"] == "config/defaults"
        assert config["structure"]["vars_dir"] == "config/variables"
        assert config["structure"]["tasks_dir"] == "playbooks/tasks"
        assert ".YML" in config["structure"]["yaml_extensions"]

    def test_monorepo_config(self, config_examples_path):
        """Test monorepo configuration."""
        config_file = config_examples_path / "monorepo_config.yml"
        assert config_file.exists()

        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config["structure"]["project_type"] == "monorepo"
        assert config["structure"]["roles_dir"] == "ansible/roles"
        assert config["structure"]["collections_dir"] == "ansible/collections"
        assert config["structure"]["playbooks_dir"] == "ansible/playbooks"


class TestProjectStructureWithConfig:
    """Test ProjectStructure class with various configurations."""

    def test_load_custom_config(self, config_examples_path, tmp_path):
        """Test loading custom configuration."""
        from docsible.utils.project_structure import ProjectStructure

        # Copy custom config to temp directory
        config_file = config_examples_path / "custom_directories_config.yml"
        import shutil

        shutil.copy(config_file, tmp_path / ".docsible.yml")

        # Create structure
        ps = ProjectStructure(tmp_path)

        # Verify custom paths are used
        defaults_dir = ps.get_defaults_dir(tmp_path)
        assert "config/defaults" in str(defaults_dir)

    def test_standard_config_detection(self, tmp_path):
        """Test that standard directories are detected without config."""
        from docsible.utils.project_structure import ProjectStructure

        # Create standard role structure
        (tmp_path / "defaults").mkdir()
        (tmp_path / "tasks").mkdir()
        (tmp_path / "meta").mkdir()

        ps = ProjectStructure(tmp_path)

        # Should detect as standard role
        assert ps.project_type in ["role", "standard"]

    def test_monorepo_config_detection(self, config_examples_path, tmp_path):
        """Test monorepo configuration detection."""
        from docsible.utils.project_structure import ProjectStructure

        # Copy monorepo config
        config_file = config_examples_path / "monorepo_config.yml"
        import shutil

        shutil.copy(config_file, tmp_path / ".docsible.yml")

        # Create monorepo structure
        (tmp_path / "ansible" / "roles").mkdir(parents=True)
        (tmp_path / "ansible" / "collections").mkdir(parents=True)

        ps = ProjectStructure(tmp_path)

        # Verify monorepo detection
        roles_dir = ps.get_roles_dir()
        assert "ansible/roles" in str(roles_dir)


class TestConfigValidation:
    """Test configuration validation."""

    def test_invalid_yaml_handling(self, tmp_path):
        """Test handling of invalid YAML in config file."""
        from docsible.utils.project_structure import ProjectStructure

        # Create invalid YAML
        config_path = tmp_path / ".docsible.yml"
        config_path.write_text("invalid: yaml: content: [")

        # Should not crash, fall back to defaults
        ps = ProjectStructure(tmp_path)
        assert ps.config is not None

    def test_missing_keys_use_defaults(self, tmp_path):
        """Test that missing keys in config use default values."""
        from docsible.utils.project_structure import ProjectStructure

        # Create config with only some keys
        config_path = tmp_path / ".docsible.yml"
        config_content = {"structure": {"defaults_dir": "my_defaults"}}
        with open(config_path, "w") as f:
            yaml.dump(config_content, f)

        ps = ProjectStructure(tmp_path)

        # Should use custom defaults_dir
        defaults_dir = ps.get_defaults_dir(tmp_path)
        assert "my_defaults" in str(defaults_dir)

        # Should use default for tasks_dir
        tasks_dir = ps.get_tasks_dir(tmp_path)
        assert "tasks" in str(tasks_dir)
