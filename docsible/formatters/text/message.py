# docsible/formatters/text/message.py
import re

from docsible.models.enhancement import Difficulty, Enhancement
from docsible.models.recommendation import Recommendation


class MessageTransformer:
    """Transform negative messages to positive framing."""

    # Transformation patterns
    PATTERNS = {
        # Pattern: (negative regex, positive template, difficulty, time)
        r"(?:Role has )?no examples directory": (
            "Add examples/ directory to help users get started",
            Difficulty.QUICK,
            "5 min",
        ),
        r"(?:Missing|No) meta/main\.yml": (
            "Add meta/main.yml for Galaxy publishing and dependencies",
            Difficulty.QUICK,
            "10 min",
        ),
        r"(?:No )?task descriptions?": (
            "Document tasks with comments for better maintainability",
            Difficulty.MEDIUM,
            "15 min",
        ),
        r"Variable(?:s)? (?:not )?documented": (
            "Document variables in defaults/main.yml for clarity",
            Difficulty.MEDIUM,
            "20 min",
        ),
        r"Consider adding (?:a )?README": (
            "README documentation helps users understand your role",
            Difficulty.QUICK,
            "Generated automatically!",
        ),
    }

    def transform(self, recommendation: Recommendation) -> Enhancement:
        """Transform recommendation to positive enhancement.

        Args:
            recommendation: Original recommendation

        Returns:
            Positively-framed enhancement
        """
        message = recommendation.message

        # Try to match transformation patterns
        for pattern, (positive_msg, difficulty, time) in self.PATTERNS.items():
            if re.search(pattern, message, re.IGNORECASE):
                # Extract action and value from positive message
                parts = positive_msg.split(" to ", 1)
                if len(parts) == 2:
                    action = parts[0]
                    value = "to " + parts[1]
                else:
                    # Try splitting on "for"
                    parts = positive_msg.split(" for ", 1)
                    if len(parts) == 2:
                        action = parts[0]
                        value = "for " + parts[1]
                    else:
                        action = positive_msg
                        value = ""
                # TODO Think about the URL thing if it is feasible if so,
                # how to get it work for any part of an ansible file.
                return Enhancement(
                    action=action,
                    value=value,
                    difficulty=difficulty,
                    time_estimate=time,
                    learn_more_url=None,
                    command=self._extract_command(recommendation),
                    priority=self._calculate_priority(recommendation),
                )

        # Fallback: use original message but make it positive
        return Enhancement(
            action=self._make_positive(message),
            value="to improve role quality",
            difficulty=Difficulty.MEDIUM,
            time_estimate="varies",
            learn_more_url=None,
            command=None,
            priority=2,
        )

    def _make_positive(self, message: str) -> str:
        """Fallback: convert negative to positive."""
        # Remove negative words
        message = re.sub(r"^(?:No|Missing|Lacks?)\s+", "", message, flags=re.IGNORECASE)
        message = re.sub(r"(?:has no|doesn't have|without)\s+", "", message, flags=re.IGNORECASE)

        # Make it an action
        if not message.startswith(("Add", "Create", "Include", "Consider")):
            message = "Add " + message

        return message

    def _extract_command(self, rec: Recommendation) -> str | None:
        """Extract command from remediation if available."""
        if rec.remediation:
            # Look for "Run:" or similar patterns
            match = re.search(r"(?:Run|Execute|Try):?\s+(.+?)(?:\n|$)", rec.remediation)
            if match:
                return match.group(1).strip()
        return None

    def _calculate_priority(self, rec: Recommendation) -> int:
        """Calculate priority based on severity and confidence."""
        from docsible.models.severity import Severity

        if rec.severity == Severity.CRITICAL:
            return 1  # High priority
        elif rec.severity == Severity.WARNING:
            return 2  # Medium priority
        else:
            return 3  # Low priority
