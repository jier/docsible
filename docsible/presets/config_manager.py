"""Persistence layer for preset configuration using YAML storage."""
import logging
import os
from pathlib import Path

import yaml

from .models import DocsiblePresetConfig

logger = logging.getLogger(__name__)

CONFIG_DIR = ".docsible"
CONFIG_FILE = "config.yml"


def resolve_config_path(base_path: Path | None = None) -> Path:
    """Resolve path to .docsible/config.yml."""
    root = Path(base_path).resolve() if base_path else Path.cwd()
    return root / CONFIG_DIR / CONFIG_FILE


class ConfigManager:
    """Read and write .docsible/config.yml."""

    def load(self, config_path: Path) -> DocsiblePresetConfig:
        """Load config from YAML. Returns empty config if file missing."""
        if not config_path.exists():
            return DocsiblePresetConfig()
        try:
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return DocsiblePresetConfig(**data)
        except Exception as e:
            logger.warning(f"Failed to load preset config from {config_path}: {e}")
            return DocsiblePresetConfig()

    def save(self, config: DocsiblePresetConfig, config_path: Path) -> None:
        """Atomically save config to YAML using write-to-temp + os.replace()."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = config.model_dump(exclude_none=False)
        tmp_path = config_path.with_suffix(".yml.tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                yaml.dump(payload, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            os.replace(tmp_path, config_path)
        except Exception as e:
            logger.error(f"Failed to save preset config: {e}")
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise
