"""Pydantic models for the Suppression System."""

import fnmatch
import re
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class SuppressionRule(BaseModel):
    """A single suppression rule that silences a matching recommendation."""

    id: str = Field(description="Short unique identifier")
    pattern: str = Field(description="Text to match in recommendation messages")
    reason: str = Field(description="Justification for suppressing this recommendation")
    file_pattern: str | None = Field(None, description="Optional file glob to scope rule")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the rule was created",
    )
    expires_at: datetime | None = Field(None, description="When the rule auto-expires")
    approved_by: str | None = Field(None, description="Name of approver")
    match_count: int = Field(default=0, description="Number of times this rule has matched")
    last_matched: datetime | None = Field(None, description="Timestamp of last match")
    use_regex: bool = Field(default=False, description="Treat pattern as a regex")

    @field_validator("pattern")
    @classmethod
    def pattern_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("pattern must not be empty")
        return v.strip()

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reason must not be empty")
        return v.strip()

    def is_expired(self) -> bool:
        """Return True if this rule has passed its expiry date."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def matches_message(self, message: str) -> bool:
        """Check if this rule's pattern matches the given recommendation message."""
        if self.use_regex:
            return bool(re.search(self.pattern, message, re.IGNORECASE))
        return self.pattern.lower() in message.lower()

    def matches_file(self, file_path: str | None) -> bool:
        """Check if this rule's file_pattern matches the given file path."""
        if self.file_pattern is None:
            return True
        if file_path is None:
            return False
        return fnmatch.fnmatch(file_path, self.file_pattern)


class SuppressionStore(BaseModel):
    """Container for all suppression rules, maps to suppress.yml."""

    rules: list[SuppressionRule] = Field(default_factory=list)

    def find_by_id(self, rule_id: str) -> SuppressionRule | None:
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def remove_by_id(self, rule_id: str) -> bool:
        """Remove a rule by ID. Returns True if found and removed."""
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]
        return len(self.rules) < before

    def expired_rules(self) -> list[SuppressionRule]:
        return [r for r in self.rules if r.is_expired()]

    def active_rules(self) -> list[SuppressionRule]:
        return [r for r in self.rules if not r.is_expired()]
