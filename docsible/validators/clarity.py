import re
from typing import Any

from .base import BaseValidator
from .models import ValidationIssue, ValidationSeverity, ValidationType


class ClarityValidator(BaseValidator):
    type = ValidationType.CLARITY

    def validate(self, documentation, role_info, complexity_report) -> tuple[list[ValidationIssue], dict[str, Any]]:
        """
        Validate documentation clarity and readability.

        Checks:
        - Has proper markdown structure
        - Has clear section headings
        - Has reasonable line lengths
        - Has code blocks properly formatted
        - Avoids excessive jargon
        """
        issues: list[ValidationIssue] = []
        metrics: dict[str, Any] = {}

        lines = documentation.split("\n")
        metrics["total_lines"] = len(lines)

        # Check for main sections
        required_sections = [
            "Description",
            "Requirements",
            "Variables",
            "Dependencies",
            "Example",
        ]
        found_sections = []
        for section in required_sections:
            if re.search(
                rf"^#+\s+{section}", documentation, re.MULTILINE | re.IGNORECASE
            ):
                found_sections.append(section)

        metrics["sections_found"] = len(found_sections)
        metrics["sections_expected"] = len(required_sections)

        missing_sections = set(required_sections) - set(found_sections)
        if missing_sections and len(found_sections) < 3:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.WARNING,
                    message=f"Missing common sections: {', '.join(missing_sections)}",
                    suggestion="Consider adding standard sections for better organization",
                )
            )

        # Check for overly long lines (readability)
        long_lines = 0
        for line in lines:
            # Ignore code blocks and tables
            if line.strip().startswith("```") or line.strip().startswith("|"):
                continue
            if len(line) > 120:
                long_lines += 1

        metrics["long_lines"] = long_lines
        if long_lines > len(lines) * 0.2:  # More than 20% of lines
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.INFO,
                    message=f"Found {long_lines} lines exceeding 120 characters",
                    suggestion="Consider breaking long lines for better readability",
                )
            )

        # Check for proper code block formatting
        code_blocks = re.findall(r"```(\w*)\n(.*?)```", documentation, re.DOTALL)
        metrics["code_blocks"] = len(code_blocks)

        unlabeled_blocks = sum(1 for lang, _ in code_blocks if not lang)
        if unlabeled_blocks > 0:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.INFO,
                    message=f"Found {unlabeled_blocks} unlabeled code blocks",
                    suggestion="Add language labels to code blocks (e.g., ```yaml, ```bash)",
                )
            )

        # Check for heading structure (should start with # and be hierarchical)
        headings = re.findall(r"^(#+)\s+(.+)$", documentation, re.MULTILINE)
        metrics["headings"] = len(headings)

        if len(headings) == 0:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.ERROR,
                    message="No markdown headings found",
                    suggestion="Add structured headings to organize content",
                )
            )

        return issues, metrics