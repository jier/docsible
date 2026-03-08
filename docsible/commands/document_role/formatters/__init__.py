"""Backward-compatibility shim. Import from docsible.formatters.text instead."""
from docsible.formatters.text.dry_run import DryRunFormatter

__all__ = ["DryRunFormatter"]
