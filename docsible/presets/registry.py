"""Built-in preset definitions."""
from .models import Preset

_PRESETS: dict[str, Preset] = {
    "personal": Preset(
        name="personal",
        description="Solo developers and learning — fast, minimal output",
        settings={
            "generate_graph": False,
            "minimal": True,
            "validate_markdown": True,
            "strict_validation": False,
            "auto_fix": False,
            "no_backup": True,
            "complexity_report": False,
            "simplification_report": False,
            "show_dependencies": False,
            "positive_framing": True,
            "comments": False,
            "task_line": False,
            "include_complexity": False,
        },
    ),
    "team": Preset(
        name="team",
        description="Team collaboration — comprehensive docs, smart defaults",
        settings={
            "validate_markdown": True,
            "strict_validation": False,
            "auto_fix": True,
            "no_backup": False,
            "complexity_report": False,
            "simplification_report": False,
            "positive_framing": True,
            "comments": True,
            "task_line": False,
            "include_complexity": False,
            # generate_graph and show_dependencies intentionally omitted -> smart defaults apply
        },
    ),
    "enterprise": Preset(
        name="enterprise",
        description="Production and compliance — full validation, all reports",
        settings={
            "generate_graph": True,
            "minimal": False,
            "validate_markdown": True,
            "strict_validation": True,
            "auto_fix": False,
            "no_backup": False,
            "complexity_report": True,
            "simplification_report": True,
            "show_dependencies": True,
            "positive_framing": True,
            "comments": True,
            "task_line": True,
            "include_complexity": True,
        },
    ),
    "consultant": Preset(
        name="consultant",
        description="Client deliverables — maximum detail, all diagrams",
        settings={
            "generate_graph": True,
            "minimal": False,
            "validate_markdown": True,
            "strict_validation": False,
            "auto_fix": False,
            "no_backup": False,
            "complexity_report": True,
            "simplification_report": True,
            "show_dependencies": True,
            "positive_framing": True,
            "comments": True,
            "task_line": True,
            "include_complexity": True,
        },
    ),
}


class PresetRegistry:
    """Registry of built-in presets."""

    @staticmethod
    def get(name: str) -> Preset:
        if name not in _PRESETS:
            raise KeyError(f"Unknown preset: {name!r}. Available: {list(_PRESETS)}")
        return _PRESETS[name]

    @staticmethod
    def list_all() -> list[Preset]:
        return list(_PRESETS.values())

    @staticmethod
    def names() -> list[str]:
        return list(_PRESETS.keys())
