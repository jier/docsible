from collections.abc import Sequence

from docsible.models.recommendation import Recommendation
from docsible.models.severity import Severity


class RecommendationFormatter:
    """Format recommendations with severity grouping."""

    def format_recommendations(
        self,
        recommendations: Sequence[Recommendation],
        show_info: bool = True,
    ) -> str:
        """Format recommendations grouped by severity.

        Args:
            recommendations: List of recommendations
            show_info: Whether to show INFO level (default: True)

        Returns:
            Formatted string output
        """
        if not recommendations:
            return "✅ No recommendations - role follows best practices!"

        # Group by severity
        grouped = self._group_by_severity(recommendations)

        # Build output
        lines = []
        lines.append("")
        lines.append("=" * 70)
        lines.append("📋 RECOMMENDATIONS")
        lines.append("=" * 70)
        lines.append("")

        # Critical first
        if Severity.CRITICAL in grouped:
            lines.extend(self._format_severity_group(
                Severity.CRITICAL,
                grouped[Severity.CRITICAL],
                "Must fix before production"
            ))
            lines.append("")

        # Then warnings
        if Severity.WARNING in grouped:
            lines.extend(self._format_severity_group(
                Severity.WARNING,
                grouped[Severity.WARNING],
                "Should fix for quality"
            ))
            lines.append("")

        # Finally info (if enabled)
        if show_info and Severity.INFO in grouped:
            lines.extend(self._format_severity_group(
                Severity.INFO,
                grouped[Severity.INFO],
                "Consider for enhancement"
            ))
            lines.append("")

        # Summary
        lines.extend(self._format_summary(grouped, show_info))
        lines.append("=" * 70)
        lines.append("")

        return "\n".join(lines)

    def _group_by_severity(
        self,
        recommendations: Sequence[Recommendation]
    ) -> dict[Severity, list[Recommendation]]:
        """Group recommendations by severity level."""
        grouped: dict[Severity, list[Recommendation]] = {}

        for rec in recommendations:
            if rec.severity not in grouped:
                grouped[rec.severity] = []
            grouped[rec.severity].append(rec)

        # Sort within each severity by confidence (highest first)
        for severity in grouped:
            grouped[severity].sort(key=lambda r: r.confidence, reverse=True)

        return grouped

    def _format_severity_group(
        self,
        severity: Severity,
        recommendations: list[Recommendation],
        subtitle: str,
    ) -> list[str]:
        """Format a group of recommendations at same severity."""
        lines = []

        # Header
        lines.append(f"{severity.icon} {severity.label} ({subtitle}):")

        # Each recommendation
        for idx, rec in enumerate(recommendations, 1):
            lines.append(f"   {idx}. {rec.message}")

            # Location if available
            if rec.location:
                lines.append(f"      📍 {rec.location}")

            # Remediation if available
            if rec.remediation:
                lines.append(f"      💡 Fix: {rec.remediation}")

        return lines

    def _format_summary(
        self,
        grouped: dict[Severity, list[Recommendation]],
        show_info: bool,
    ) -> list[str]:
        """Format summary line."""
        lines = []

        critical_count = len(grouped.get(Severity.CRITICAL, []))
        warning_count = len(grouped.get(Severity.WARNING, []))
        info_count = len(grouped.get(Severity.INFO, []))

        lines.append("📊 Summary:")
        lines.append(f"   🔴 {critical_count} critical issues")
        lines.append(f"   🟡 {warning_count} warnings")
        if show_info:
            lines.append(f"   💡 {info_count} suggestions")
        else:
            lines.append(f"   💡 {info_count} suggestions (hidden, use --show-info)")

        return lines