"""
Markdown formatting validator for generated documentation.

Validates raw markdown formatting for human readability:
- Whitespace (consecutive blank lines, trailing spaces, tabs)
- Table structure (column alignment, separators)
- Syntax correctness (unclosed code blocks, heading hierarchy)
"""

import logging
import re
from typing import Any

from .doc_validator import ValidationIssue, ValidationSeverity, ValidationType

logger = logging.getLogger(__name__)


class MarkdownValidator:
    """Validates raw markdown formatting for human readability."""

    def __init__(self, max_consecutive_blanks: int = 2, max_line_length: int = 120):
        """
        Initialize markdown validator.

        Args:
            max_consecutive_blanks: Maximum allowed consecutive blank lines
            max_line_length: Maximum line length for readability warnings
        """
        self.max_consecutive_blanks = max_consecutive_blanks
        self.max_line_length = max_line_length

    def validate_whitespace(self, markdown: str) -> list[ValidationIssue]:
        """
        Check for excessive whitespace issues.

        Detects:
        - More than N consecutive blank lines
        - Trailing whitespace on lines
        - Tab characters (should be spaces in markdown)

        Args:
            markdown: Raw markdown content

        Returns:
            List of validation issues found
        """
        issues: list[ValidationIssue] = []
        lines = markdown.split("\n")

        # Check for excessive consecutive blank lines
        blank_count = 0
        blank_line_start = None

        for i, line in enumerate(lines, 1):
            if line.strip() == "":
                if blank_count == 0:
                    blank_line_start = i
                blank_count += 1
            else:
                if blank_count > self.max_consecutive_blanks:
                    issues.append(
                        ValidationIssue(
                            type=ValidationType.CLARITY,
                            severity=ValidationSeverity.WARNING,
                            message=f"Excessive blank lines: {blank_count} consecutive empty lines (max: {self.max_consecutive_blanks})",
                            line_number=blank_line_start,
                            suggestion=f"Reduce to maximum {self.max_consecutive_blanks} blank lines for better readability",
                        )
                    )
                blank_count = 0

        # Check for trailing whitespace
        trailing_lines = [i for i, line in enumerate(lines, 1) if line != line.rstrip()]
        if len(trailing_lines) > 10:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.INFO,
                    message=f"Found {len(trailing_lines)} lines with trailing whitespace",
                    line_number=trailing_lines[0] if trailing_lines else None,
                    suggestion="Remove trailing spaces for cleaner output (use --auto-fix)",
                )
            )

        # Check for tab characters (should be spaces in markdown)
        tab_lines = [i for i, line in enumerate(lines, 1) if "\t" in line]
        if tab_lines:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.WARNING,
                    message=f"Found tab characters on {len(tab_lines)} lines",
                    line_number=tab_lines[0] if tab_lines else None,
                    suggestion="Replace tabs with spaces for consistent rendering",
                )
            )

        return issues

    def validate_tables(self, markdown: str) -> list[ValidationIssue]:
        """
        Validate markdown table formatting.

        Detects:
        - Column count mismatch between header and separator
        - Malformed separator rows
        - Inconsistent column counts in data rows

        Args:
            markdown: Raw markdown content

        Returns:
            List of validation issues found
        """
        issues: list[ValidationIssue] = []
        lines = markdown.split("\n")

        in_table = False
        table_start: int| None = None
        table_lines: list[Any] = []
        separator_line = None
        header_line = None

        for i, line in enumerate(lines, 1):
            # Detect table rows (starts and ends with |)
            if line.strip().startswith("|") and line.strip().endswith("|"):
                if not in_table:
                    in_table = True
                    table_start = i
                    table_lines: list[Any] = []
                    separator_line = None
                    header_line = None

                table_lines.append((i, line))

                # Detect separator row (contains only |, -, :, and spaces)
                if re.match(r"^\s*\|[\s\-|:]+\|\s*$", line):
                    separator_line = (i, line)
                    if table_lines and len(table_lines) >= 2:
                        header_line = table_lines[-2]
            else:
                if in_table:
                    # End of table - validate it
                    if isinstance(table_start, int):
                        issues.extend(
                            self._validate_single_table(
                                table_lines, header_line, separator_line, table_start
                            )
                        )
                        in_table = False

        # Validate last table if file ends with table
        if in_table:
            if isinstance(table_start, int):
                issues.extend(
                    self._validate_single_table(
                        table_lines, header_line, separator_line, table_start
                    )
                )

        return issues

    def _validate_single_table(
        self,
        table_lines: list[tuple[int, str]],
        header_line: tuple[int, str] | None,
        separator_line: tuple[int, str] | None,
        table_start: int,
    ) -> list[ValidationIssue]:
        """Validate a single markdown table."""
        issues: list[ValidationIssue] = []

        if not header_line or not separator_line:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.ERROR,
                    message="Malformed table: missing header or separator row",
                    line_number=table_start,
                    suggestion="Ensure table has header row followed by separator row (|---|---|)",
                )
            )
            return issues

        # Count columns in header
        header_text = header_line[1]
        # Split by | and count non-empty cells (accounting for leading/trailing |)
        header_parts = header_text.split("|")
        header_cols = len([c for c in header_parts if c.strip()])

        # Count separators
        sep_text = separator_line[1]
        sep_parts = sep_text.split("|")
        sep_cols = len([c for c in sep_parts if c.strip() and "-" in c])

        # Check column count mismatch
        if header_cols != sep_cols:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.ERROR,
                    message=f"Table column mismatch: header has {header_cols} columns, separator has {sep_cols}",
                    line_number=separator_line[0],
                    suggestion=f"Add {abs(header_cols - sep_cols)} separator(s) to match header columns",
                )
            )

        # Check data rows have correct column count
        for line_num, line_text in table_lines:
            # Skip header, separator, and other separator lines
            if line_num == header_line[0] or line_num == separator_line[0]:
                continue
            if re.match(r"^\s*\|[\s\-|:]+\|\s*$", line_text):
                continue

            # Count columns in data row
            data_parts = line_text.split("|")
            data_cols = len([c for c in data_parts if c.strip() or c == ""])
            # Adjust for leading/trailing pipes
            if line_text.strip().startswith("|") and line_text.strip().endswith("|"):
                data_cols = len(data_parts) - 2

            if data_cols != header_cols and abs(data_cols - header_cols) >= 1:
                issues.append(
                    ValidationIssue(
                        type=ValidationType.CLARITY,
                        severity=ValidationSeverity.WARNING,
                        message=f"Row has {data_cols} columns, expected {header_cols}",
                        line_number=line_num,
                        suggestion="Ensure all table rows have the same number of columns",
                    )
                )

        return issues

    def validate_syntax(self, markdown: str) -> list[ValidationIssue]:
        """
        Validate markdown syntax basics.

        Detects:
        - Unclosed code blocks (```...```)
        - Unclosed HTML tags (<details>, <summary>)
        - Improper heading hierarchy (skipping levels)

        Args:
            markdown: Raw markdown content

        Returns:
            List of validation issues found
        """
        issues: list[ValidationIssue] = []
        lines = markdown.split("\n")

        # Check for unclosed code blocks
        code_block_count = sum(1 for line in lines if line.strip().startswith("```"))
        if code_block_count % 2 != 0:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.ERROR,
                    message=f"Unclosed code block: found {code_block_count} code fence markers (should be even)",
                    suggestion="Ensure every ``` has a closing ```",
                )
            )

        # Check for unclosed HTML details tags
        details_open = sum(1 for line in lines if "<details>" in line.lower())
        details_close = sum(1 for line in lines if "</details>" in line.lower())
        if details_open != details_close:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.ERROR,
                    message=f"Unclosed <details> tag: {details_open} open, {details_close} close",
                    suggestion="Ensure every <details> has matching </details>",
                )
            )

        # Check for proper heading hierarchy (no skipping levels)
        heading_levels = []
        for i, line in enumerate(lines, 1):
            match = re.match(r"^(#{1,6})\s+", line)
            if match:
                level = len(match.group(1))
                heading_levels.append((i, level))

        for i in range(1, len(heading_levels)):
            prev_line, prev_level = heading_levels[i - 1]
            curr_line, curr_level = heading_levels[i]

            # Check if we jumped more than one level
            if curr_level > prev_level + 1:
                issues.append(
                    ValidationIssue(
                        type=ValidationType.CLARITY,
                        severity=ValidationSeverity.INFO,
                        message=f"Heading hierarchy skip: jumped from h{prev_level} to h{curr_level}",
                        line_number=curr_line,
                        suggestion=f"Consider using h{prev_level + 1} instead of h{curr_level}",
                    )
                )

        return issues

    def validate(self, markdown: str) -> list[ValidationIssue]:
        """
        Run all markdown formatting validations.

        Args:
            markdown: Raw markdown content

        Returns:
            List of all validation issues found
        """
        issues: list[ValidationIssue] = []
        issues.extend(self.validate_whitespace(markdown))
        issues.extend(self.validate_tables(markdown))
        issues.extend(self.validate_syntax(markdown))
        return issues
