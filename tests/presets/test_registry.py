"""Tests for docsible.presets.registry — PresetRegistry."""
import pytest

from docsible.presets.models import Preset
from docsible.presets.registry import PresetRegistry


class TestPresetRegistryGet:
    """Tests for PresetRegistry.get()."""

    def test_get_personal(self):
        p = PresetRegistry.get("personal")
        assert isinstance(p, Preset)
        assert p.name == "personal"

    def test_get_team(self):
        p = PresetRegistry.get("team")
        assert isinstance(p, Preset)
        assert p.name == "team"

    def test_get_enterprise(self):
        p = PresetRegistry.get("enterprise")
        assert isinstance(p, Preset)
        assert p.name == "enterprise"

    def test_get_consultant(self):
        p = PresetRegistry.get("consultant")
        assert isinstance(p, Preset)
        assert p.name == "consultant"

    def test_get_unknown_raises_key_error(self):
        with pytest.raises(KeyError):
            PresetRegistry.get("unknown")

    def test_get_empty_string_raises_key_error(self):
        with pytest.raises(KeyError):
            PresetRegistry.get("")

    def test_get_case_sensitive(self):
        with pytest.raises(KeyError):
            PresetRegistry.get("Personal")


class TestPresetRegistryListAll:
    """Tests for PresetRegistry.list_all()."""

    def test_list_all_returns_four_presets(self):
        presets = PresetRegistry.list_all()
        assert len(presets) == 4

    def test_list_all_returns_preset_instances(self):
        for p in PresetRegistry.list_all():
            assert isinstance(p, Preset)

    def test_list_all_contains_all_names(self):
        names = {p.name for p in PresetRegistry.list_all()}
        assert names == {"personal", "team", "enterprise", "consultant"}


class TestPresetRegistryNames:
    """Tests for PresetRegistry.names()."""

    def test_names_returns_four_items(self):
        assert len(PresetRegistry.names()) == 4

    def test_names_returns_expected_list(self):
        assert PresetRegistry.names() == ["personal", "team", "enterprise", "consultant"]

    def test_names_returns_list(self):
        assert isinstance(PresetRegistry.names(), list)


class TestEnterprisePresetSettings:
    """Verify enterprise preset has the expected settings."""

    def setup_method(self):
        self.preset = PresetRegistry.get("enterprise")

    def test_enterprise_generate_graph_true(self):
        assert self.preset.settings["generate_graph"] is True

    def test_enterprise_strict_validation_true(self):
        assert self.preset.settings["strict_validation"] is True

    def test_enterprise_complexity_report_true(self):
        assert self.preset.settings["complexity_report"] is True

    def test_enterprise_simplification_report_true(self):
        assert self.preset.settings["simplification_report"] is True

    def test_enterprise_show_dependencies_true(self):
        assert self.preset.settings["show_dependencies"] is True

    def test_enterprise_minimal_false(self):
        assert self.preset.settings["minimal"] is False

    def test_enterprise_auto_fix_false(self):
        assert self.preset.settings["auto_fix"] is False


class TestPersonalPresetSettings:
    """Verify personal preset has the expected settings."""

    def setup_method(self):
        self.preset = PresetRegistry.get("personal")

    def test_personal_minimal_true(self):
        assert self.preset.settings["minimal"] is True

    def test_personal_generate_graph_false(self):
        assert self.preset.settings["generate_graph"] is False

    def test_personal_strict_validation_false(self):
        assert self.preset.settings["strict_validation"] is False

    def test_personal_complexity_report_false(self):
        assert self.preset.settings["complexity_report"] is False


class TestTeamPresetSettings:
    """Verify team preset smart-default behaviour."""

    def setup_method(self):
        self.preset = PresetRegistry.get("team")

    def test_team_does_not_have_generate_graph_key(self):
        """generate_graph intentionally omitted so smart defaults apply."""
        assert "generate_graph" not in self.preset.settings

    def test_team_does_not_have_show_dependencies_key(self):
        """show_dependencies intentionally omitted so smart defaults apply."""
        assert "show_dependencies" not in self.preset.settings

    def test_team_auto_fix_true(self):
        assert self.preset.settings["auto_fix"] is True

    def test_team_comments_true(self):
        assert self.preset.settings["comments"] is True

    def test_team_validate_markdown_true(self):
        assert self.preset.settings["validate_markdown"] is True
