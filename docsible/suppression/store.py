"""Persistence layer for suppression rules using YAML storage."""

import logging
import os
from datetime import datetime
from pathlib import Path

import yaml

from docsible.models.suppression import SuppressionRule, SuppressionStore

logger = logging.getLogger(__name__)

SUPPRESS_DIR = ".docsible"
SUPPRESS_FILE = "suppress.yml"


def resolve_suppress_path(base_path: Path | None = None) -> Path:
    """Resolve the path to suppress.yml.

    Priority:
    1. <base_path>/.docsible/suppress.yml
    2. <cwd>/.docsible/suppress.yml
    """
    root = Path(base_path).resolve() if base_path else Path.cwd()
    return root / SUPPRESS_DIR / SUPPRESS_FILE


def load_store(suppress_path: Path) -> SuppressionStore:
    """Load SuppressionStore from YAML file. Returns empty store if file missing."""
    if not suppress_path.exists():
        return SuppressionStore()

    try:
        with open(suppress_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        rules_data = data.get("rules", [])
        rules = [SuppressionRule(**r) for r in rules_data]
        return SuppressionStore(rules=rules)
    except Exception as e:
        logger.warning(f"Failed to load suppression store from {suppress_path}: {e}")
        return SuppressionStore()


def save_store(store: SuppressionStore, suppress_path: Path) -> None:
    """Atomically save SuppressionStore to YAML using write-to-temp + os.replace()."""
    suppress_path.parent.mkdir(parents=True, exist_ok=True)

    rules_data = []
    for rule in store.rules:
        d = rule.model_dump()
        for key in ("created_at", "expires_at", "last_matched"):
            if d[key] is not None and isinstance(d[key], datetime):
                d[key] = d[key].isoformat()
        rules_data.append(d)

    payload = {"rules": rules_data}
    tmp_path = suppress_path.with_suffix(".yml.tmp")

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            yaml.dump(payload, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        os.replace(tmp_path, suppress_path)
    except Exception as e:
        logger.error(f"Failed to save suppression store: {e}")
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
