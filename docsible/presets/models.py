"""Pydantic models for the Preset System."""
from typing import Any, Literal

from pydantic import BaseModel, Field

PresetName = Literal["personal", "team", "enterprise", "consultant"]


class Preset(BaseModel):
    """A named documentation preset with bundled option values."""
    name: str
    description: str
    settings: dict[str, Any] = Field(default_factory=dict)
    model_config = {"frozen": True}


class DocsiblePresetConfig(BaseModel):
    """Content of .docsible/config.yml — written by `docsible init`."""
    preset: str | None = None
    overrides: dict[str, Any] = Field(default_factory=dict)
    ci_cd: dict[str, Any] = Field(default_factory=dict)
