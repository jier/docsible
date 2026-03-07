from enum import Enum

from pydantic import BaseModel, Field


class Difficulty(Enum):
    """Difficulty level for enhancements."""

    QUICK = "quick"  # < 5 minutes
    MEDIUM = "medium"  # 5-30 minutes
    ADVANCED = "advanced"  # > 30 minutes


class Enhancement(BaseModel):
    """Positively-framed enhancement opportunity."""

    action: str = Field(description="What to do (e.g., 'Add examples/')")
    value: str = Field(description="Why it matters (e.g., 'help users get started')")
    difficulty: Difficulty = Field(description="How hard (Quick/Medium/Advanced)")
    time_estimate: str = Field(description="How long (e.g., '5 min')")

    # Optional fields
    command: str | None = Field(None, description="Command to run")
    learn_more_url: str | None = Field(None, description="Documentation URL")
    priority: int = Field(default=1, description="Priority (1=high, 3=low)")

    @property
    def formatted_message(self) -> str:
        """Format as positive enhancement message."""
        msg = f"{self.action} {self.value} ({self.difficulty.value.title()}: {self.time_estimate})"
        if self.command:
            msg += f"\n      → Run: {self.command}"
        return msg
