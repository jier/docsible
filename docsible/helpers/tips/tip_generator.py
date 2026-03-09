"""Contextual tip generator for docsible."""

import random


class TipGenerator:
    """Generate contextual tips based on user's situation."""

    TIPS: dict[str, list[str]] = {
        "first_run": [
            "Tip: Run 'docsible init' to set up smart defaults for your project",
            "Tip: Use --graph to visualize complex task flows",
            "Tip: Add examples/ directory to help users get started",
        ],
        "simple_role": [
            "Tip: Simple roles use minimal docs by default (smart defaults)",
            "Tip: Run 'docsible role --role . --analyze-only' to see complexity metrics",
            "Tip: Add examples/ directory to help users get started quickly",
        ],
        "complex_role": [
            "Tip: Complex roles automatically get graph generation enabled",
            "Tip: Consider splitting large roles into smaller, focused roles",
            "Tip: Use 'docsible role --role . --complexity-report' to check quality",
        ],
        "after_generation": [
            "Tip: Use --show-info to see all enhancement suggestions",
            "Tip: Try 'docsible guide getting-started' for a full walkthrough",
            "Tip: Share your role on Ansible Galaxy!",
        ],
        "general": [
            "Tip: Use --graph to generate task flow diagrams",
            "Tip: Run 'docsible guide getting-started' for an interactive walkthrough",
            "Tip: Use --minimal for quick documentation of simple roles",
        ],
    }

    @classmethod
    def get_tip(cls, context: str = "general") -> str | None:
        """Get a random tip for the given context.

        Args:
            context: Tip context (first_run, simple_role, complex_role, after_generation, general)

        Returns:
            Random tip string, or None if no tips for context
        """
        tips = cls.TIPS.get(context, cls.TIPS.get("general", []))
        return random.choice(tips) if tips else None

    @classmethod
    def get_all_tips(cls, context: str = "general") -> list[str]:
        """Get all tips for the given context.

        Args:
            context: Tip context

        Returns:
            List of all tips for the context
        """
        return cls.TIPS.get(context, cls.TIPS.get("general", []))

    @classmethod
    def get_available_contexts(cls) -> list[str]:
        """Return list of available tip contexts."""
        return list(cls.TIPS.keys())
