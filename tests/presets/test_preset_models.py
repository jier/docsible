"""Tests for docsible.presets.models — Preset and DocsiblePresetConfig."""
import pytest
from pydantic import ValidationError

from docsible.presets.models import DocsiblePresetConfig, Preset


class TestPreset:
    """Tests for the Preset model."""

    def test_preset_creation_all_fields(self):
        p = Preset(
            name="test",
            description="A test preset",
            settings={"generate_graph": True, "minimal": False},
        )
        assert p.name == "test"
        assert p.description == "A test preset"
        assert p.settings == {"generate_graph": True, "minimal": False}

    def test_preset_default_settings_empty(self):
        p = Preset(name="empty", description="No settings")
        assert p.settings == {}

    def test_preset_is_frozen(self):
        """model_config = {'frozen': True} makes instances immutable."""
        p = Preset(name="frozen", description="Immutable", settings={"key": "value"})
        with pytest.raises(Exception):
            # Frozen pydantic models raise ValidationError or TypeError on assignment
            p.name = "other"  # type: ignore[misc]

    def test_preset_model_config_frozen(self):
        """Confirm the class-level frozen config is set."""
        assert Preset.model_config.get("frozen") is True

    def test_preset_settings_accepts_any_values(self):
        p = Preset(
            name="mixed",
            description="Mixed types",
            settings={"flag": True, "count": 42, "label": "hello", "nested": {"a": 1}},
        )
        assert p.settings["flag"] is True
        assert p.settings["count"] == 42
        assert p.settings["label"] == "hello"
        assert p.settings["nested"] == {"a": 1}

    def test_preset_requires_name(self):
        with pytest.raises(ValidationError):
            Preset(description="No name")  # type: ignore[call-arg]

    def test_preset_requires_description(self):
        with pytest.raises(ValidationError):
            Preset(name="no_desc")  # type: ignore[call-arg]


class TestDocsiblePresetConfig:
    """Tests for the DocsiblePresetConfig model."""

    def test_creation_with_all_fields(self):
        cfg = DocsiblePresetConfig(
            preset="team",
            overrides={"generate_graph": True},
            ci_cd={"platform": "github"},
        )
        assert cfg.preset == "team"
        assert cfg.overrides == {"generate_graph": True}
        assert cfg.ci_cd == {"platform": "github"}

    def test_default_preset_is_none(self):
        cfg = DocsiblePresetConfig()
        assert cfg.preset is None

    def test_default_overrides_is_empty_dict(self):
        cfg = DocsiblePresetConfig()
        assert cfg.overrides == {}
        assert isinstance(cfg.overrides, dict)

    def test_default_ci_cd_is_empty_dict(self):
        cfg = DocsiblePresetConfig()
        assert cfg.ci_cd == {}
        assert isinstance(cfg.ci_cd, dict)

    def test_preset_accepts_none(self):
        cfg = DocsiblePresetConfig(preset=None)
        assert cfg.preset is None

    def test_preset_accepts_string(self):
        for name in ("personal", "team", "enterprise", "consultant"):
            cfg = DocsiblePresetConfig(preset=name)
            assert cfg.preset == name

    def test_overrides_field_type(self):
        cfg = DocsiblePresetConfig(overrides={"key": "value", "flag": True})
        assert cfg.overrides["key"] == "value"
        assert cfg.overrides["flag"] is True

    def test_ci_cd_field_type(self):
        cfg = DocsiblePresetConfig(ci_cd={"platform": "gitlab", "branch": "main"})
        assert cfg.ci_cd["platform"] == "gitlab"

    def test_defaults_do_not_share_mutable_state(self):
        """Two instances should not share the same dict objects."""
        cfg1 = DocsiblePresetConfig()
        cfg2 = DocsiblePresetConfig()
        cfg1.overrides["new_key"] = "value"
        assert "new_key" not in cfg2.overrides
