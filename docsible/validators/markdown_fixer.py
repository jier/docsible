"""
Markdown formatting auto-fixer.

Automatically fixes common markdown formatting issues:
- Excessive whitespace (consecutive blank lines, trailing spaces)
- Table spacing (blank lines around tables)
- Tab characters (convert to spaces)
"""

import logging

logger = logging.getLogger(__name__)


class MarkdownFixer:
    """Automatically fix common markdown formatting issues."""

    def __init__(self, max_consecutive_blanks: int = 2):
        """
        Initialize markdown fixer.

        Args:
            max_consecutive_blanks: Maximum allowed consecutive blank lines
        """
        self.max_consecutive_blanks = max_consecutive_blanks

    def fix_excessive_whitespace(self, markdown: str) -> str:
        """
        Remove excessive blank lines (max N consecutive).

        Args:
            markdown: Raw markdown content

        Returns:
            Fixed markdown with reduced blank lines
        """
        lines = markdown.split("\n")
        fixed_lines = []
        blank_count = 0

        for line in lines:
            if line.strip() == "":
                blank_count += 1
                if blank_count <= self.max_consecutive_blanks:
                    fixed_lines.append(line)
            else:
                blank_count = 0
                fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def fix_trailing_whitespace(self, markdown: str) -> str:
        """
        Remove trailing whitespace from all lines.

        Args:
            markdown: Raw markdown content

        Returns:
            Fixed markdown with no trailing spaces
        """
        return "\n".join(line.rstrip() for line in markdown.split("\n"))

    def fix_tabs(self, markdown: str) -> str:
        """
        Replace tab characters with spaces.

        Args:
            markdown: Raw markdown content

        Returns:
            Fixed markdown with tabs converted to spaces
        """
        return markdown.replace("\t", "    ")

    def fix_table_spacing(self, markdown: str) -> str:
        """
        Ensure proper spacing around tables (blank line before and after).

        Args:
            markdown: Raw markdown content

        Returns:
            Fixed markdown with proper table spacing
        """
        lines = markdown.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            # Check if this is a table line
            is_table_line = line.strip().startswith("|") and line.strip().endswith("|")

            # Check if previous line was a table line
            prev_is_table = (
                i > 0
                and lines[i - 1].strip().startswith("|")
                and lines[i - 1].strip().endswith("|")
            )

            # Check if next line is a table line
            next_is_table = (
                i < len(lines) - 1
                and lines[i + 1].strip().startswith("|")
                and lines[i + 1].strip().endswith("|")
            )

            # Add blank line before table if missing
            if is_table_line and not prev_is_table and i > 0:
                prev_line = lines[i - 1].strip()
                if prev_line:  # Previous line has content
                    # Check if there's already a blank line
                    if not (i > 1 and lines[i - 2].strip() == ""):
                        fixed_lines.append("")  # Add blank line

            fixed_lines.append(line)

            # Add blank line after table if missing
            if is_table_line and not next_is_table and i < len(lines) - 1:
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if next_line:  # Next line has content
                    # Add blank line after this table row
                    fixed_lines.append("")

        return "\n".join(fixed_lines)

    def fix_all(self, markdown: str) -> str:
        """
        Apply all auto-fixes in the recommended order.

        Order matters:
        1. Fix tabs first (affects line content)
        2. Fix trailing whitespace (cleanup)
        3. Fix excessive whitespace (reduces blank lines)
        4. Fix table spacing (may add blank lines, but not excessive)

        Args:
            markdown: Raw markdown content

        Returns:
            Fixed markdown with all corrections applied
        """
        markdown = self.fix_tabs(markdown)
        markdown = self.fix_trailing_whitespace(markdown)
        markdown = self.fix_excessive_whitespace(markdown)
        markdown = self.fix_table_spacing(markdown)
        return markdown
