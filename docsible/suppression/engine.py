"""Core suppression filtering logic."""

import logging
from datetime import datetime, timezone
from pathlib import Path

from docsible.models.recommendation import Recommendation
from docsible.models.suppression import SuppressionRule
from docsible.suppression.store import load_store, resolve_suppress_path, save_store

logger = logging.getLogger(__name__)


def apply_suppressions(
    recommendations: list[Recommendation],
    base_path: Path | None = None,
) -> tuple[list[Recommendation], list[Recommendation]]:
    """Filter recommendations against active suppression rules.

    Args:
        recommendations: Raw recommendations from analyzers
        base_path: Role path or project root (for locating suppress.yml)

    Returns:
        Tuple of (visible_recommendations, suppressed_recommendations)
    """
    suppress_path = resolve_suppress_path(base_path)
    store = load_store(suppress_path)

    # Warn about expired suppression rules
    expired = store.expired_rules()
    if expired:
        logger.warning(
            f"  Warning: {len(expired)} suppression rule(s) have expired"
            f" — run 'docsible suppress clean' to remove.",
        )
        for rule in expired:
            expiry_date = rule.expires_at.date() if rule.expires_at else "unknown"
            logger.warning(f"    [{rule.id}] \"{rule.pattern}\" expired {expiry_date}")

    # Warn about never-matched rules older than 30 days
    from datetime import timedelta
    stale_threshold = datetime.now(timezone.utc) - timedelta(days=30)
    never_matched = [
        r for r in store.active_rules()
        if r.match_count == 0 and r.created_at < stale_threshold
    ]
    if never_matched:
        logger.warning(
            f"  Warning: {len(never_matched)} suppression rule(s) have never matched any recommendation:",
        )
        for rule in never_matched:
            logger.warning(
                f"    [{rule.id}] \"{rule.pattern}\" — consider 'docsible suppress remove {rule.id}'",
            )

    active_rules = store.active_rules()

    if not active_rules:
        return recommendations, []

    visible = []
    suppressed = []
    store_dirty = False

    for rec in recommendations:
        matched_rule = _find_matching_rule(rec, active_rules)
        if matched_rule:
            suppressed.append(rec)
            matched_rule.match_count += 1
            matched_rule.last_matched = datetime.now(timezone.utc)
            store_dirty = True
            logger.debug(f"Suppressed recommendation '{rec.message}' via rule {matched_rule.id}")
        else:
            visible.append(rec)

    if store_dirty:
        try:
            save_store(store, suppress_path)
        except Exception as e:
            logger.warning(f"Could not update suppression match counts: {e}")

    return visible, suppressed


def _find_matching_rule(
    rec: Recommendation,
    rules: list[SuppressionRule],
) -> SuppressionRule | None:
    """Find the first active rule that matches this recommendation."""
    for rule in rules:
        if rule.matches_message(rec.message) and rule.matches_file(rec.file_path):
            return rule
    return None
