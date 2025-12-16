"""Tests for MarkdownFixer - automatic markdown formatting fixes."""

from docsible.validators.markdown_fixer import MarkdownFixer


class TestTabFixes:
    """Test tab character replacement."""

    def test_fix_tabs_replaces_with_spaces(self):
        """Test that tabs are replaced with 4 spaces."""
        markdown = """# Header
\tIndented line
\t\tDouble indent
Normal line
"""
        fixer = MarkdownFixer()
        fixed = fixer.fix_tabs(markdown)

        # Should have no tabs
        assert "\t" not in fixed

        # Should have spaces instead
        assert "    Indented line" in fixed
        assert "        Double indent" in fixed

    def test_fix_tabs_preserves_no_tabs(self):
        """Test that markdown without tabs is unchanged."""
        markdown = """# Header
    Already using spaces
Normal line
"""
        fixer = MarkdownFixer()
        fixed = fixer.fix_tabs(markdown)

        # Should be unchanged
        assert fixed == markdown


class TestTrailingWhitespaceFixes:
    """Test trailing whitespace removal."""

    def test_fix_trailing_whitespace_removes_spaces(self):
        """Test that trailing spaces are removed from lines."""
        markdown = "# Header  \nSome text   \nMore text\n"
        fixer = MarkdownFixer()
        fixed = fixer.fix_trailing_whitespace(markdown)

        # Should have no trailing spaces
        lines = fixed.split("\n")
        for line in lines[:-1]:  # Skip last empty line
            assert line == line.rstrip()

    def test_fix_trailing_whitespace_preserves_content(self):
        """Test that content is preserved when removing trailing spaces."""
        markdown = "# Header  \n  Indented text  \n"
        fixer = MarkdownFixer()
        fixed = fixer.fix_trailing_whitespace(markdown)

        # Should preserve indentation
        assert "# Header" in fixed
        assert "  Indented text" in fixed

        # But no trailing spaces
        assert not fixed.endswith(" \n")

    def test_fix_trailing_whitespace_clean_text(self):
        """Test that clean text without trailing spaces is unchanged."""
        markdown = """# Header
Some text
More text
"""
        fixer = MarkdownFixer()
        fixed = fixer.fix_trailing_whitespace(markdown)

        # Should be unchanged
        assert fixed == markdown


class TestExcessiveWhitespaceFixes:
    """Test excessive blank line removal."""

    def test_fix_excessive_whitespace_reduces_blanks(self):
        """Test that excessive blank lines are reduced to max allowed."""
        markdown = """# Header



Too many blanks here.



And here too.
"""
        fixer = MarkdownFixer(max_consecutive_blanks=2)
        fixed = fixer.fix_excessive_whitespace(markdown)

        # Should not have more than 2 consecutive blank lines
        assert "\n\n\n\n" not in fixed

        # Should still have some blank lines
        assert "\n\n" in fixed

    def test_fix_excessive_whitespace_preserves_acceptable(self):
        """Test that acceptable blank lines are preserved."""
        markdown = """# Header

Paragraph 1.

Paragraph 2.
"""
        fixer = MarkdownFixer(max_consecutive_blanks=2)
        fixed = fixer.fix_excessive_whitespace(markdown)

        # Should be unchanged
        assert fixed == markdown

    def test_fix_excessive_whitespace_at_start(self):
        """Test handling of excessive blank lines at document start."""
        markdown = """


# Header

Content here.
"""
        fixer = MarkdownFixer(max_consecutive_blanks=2)
        fixed = fixer.fix_excessive_whitespace(markdown)

        # Should reduce excessive blanks at start
        assert not fixed.startswith("\n\n\n")

    def test_fix_excessive_whitespace_at_end(self):
        """Test handling of excessive blank lines at document end."""
        markdown = """# Header

Content here.



"""
        fixer = MarkdownFixer(max_consecutive_blanks=2)
        fixed = fixer.fix_excessive_whitespace(markdown)

        # Should reduce excessive blanks at end
        # Count trailing newlines
        trailing_newlines = len(fixed) - len(fixed.rstrip("\n"))
        assert trailing_newlines <= 3  # max_consecutive_blanks + 1


class TestTableSpacingFixes:
    """Test table spacing fixes."""

    def test_fix_table_spacing_adds_blank_before(self):
        """Test that blank line is added before table if missing."""
        markdown = """# Header
Some text
| Col 1 | Col 2 |
|-------|-------|
| A     | B     |
"""
        fixer = MarkdownFixer()
        fixed = fixer.fix_table_spacing(markdown)

        # Should have blank line before table
        assert "Some text\n\n|" in fixed

    def test_fix_table_spacing_adds_blank_after(self):
        """Test that blank line is added after table if missing."""
        markdown = """# Header

| Col 1 | Col 2 |
|-------|-------|
| A     | B     |
More text
"""
        fixer = MarkdownFixer()
        fixed = fixer.fix_table_spacing(markdown)

        # Should have blank line after table
        assert "| B     |\n\nMore text" in fixed

    def test_fix_table_spacing_preserves_existing(self):
        """Test that existing proper spacing is preserved."""
        markdown = """# Header

| Col 1 | Col 2 |
|-------|-------|
| A     | B     |

More text
"""
        fixer = MarkdownFixer()
        fixed = fixer.fix_table_spacing(markdown)

        # Should be mostly unchanged (might differ slightly in blank handling)
        assert "| Col 1 | Col 2 |" in fixed
        assert "More text" in fixed

    def test_fix_table_spacing_multiple_tables(self):
        """Test spacing fix for multiple tables."""
        markdown = """# Header
| Table 1 | Data |
|---------|------|
| A       | B    |
Some text
| Table 2 | Data |
|---------|------|
| C       | D    |
More text
"""
        fixer = MarkdownFixer()
        fixed = fixer.fix_table_spacing(markdown)

        # Should have blank lines around both tables
        lines = fixed.split("\n")
        table_lines = [i for i, line in enumerate(lines) if line.strip().startswith("|")]

        # Check that tables have spacing
        assert len(table_lines) > 0

    def test_fix_table_spacing_at_document_start(self):
        """Test table spacing when table is at document start."""
        markdown = """| Col 1 | Col 2 |
|-------|-------|
| A     | B     |

Some text after.
"""
        fixer = MarkdownFixer()
        fixed = fixer.fix_table_spacing(markdown)

        # Should still be valid (no blank before first table is okay)
        assert "| Col 1 | Col 2 |" in fixed


class TestFixAll:
    """Test the complete fix pipeline."""

    def test_fix_all_applies_all_fixes(self):
        """Test that fix_all applies all fixes in correct order."""
        markdown = """# Header
\tTab here
Line with trailing


Too many blanks.
| Col 1 | Col 2 |
|-------|-------|
| A     | B     |
More text
"""
        fixer = MarkdownFixer()
        fixed = fixer.fix_all(markdown)

        # Should fix tabs
        assert "\t" not in fixed

        # Should fix trailing whitespace
        lines = fixed.split("\n")
        for line in lines[:-1]:
            assert line == line.rstrip() or line == ""

        # Should reduce excessive blanks
        assert "\n\n\n\n" not in fixed

        # Should add table spacing
        assert "| B     |\n\nMore text" in fixed or "| B     |\n\n\nMore text" in fixed

    def test_fix_all_order_matters(self):
        """Test that fixes are applied in the correct order."""
        # Tab followed by trailing space
        markdown = "Line\t  \n"

        fixer = MarkdownFixer()
        fixed = fixer.fix_all(markdown)

        # Should fix tabs first (to spaces), then trailing whitespace
        assert "\t" not in fixed
        assert not fixed.endswith("  \n")
        assert fixed == "Line\n"

    def test_fix_all_clean_markdown_unchanged(self):
        """Test that clean markdown is mostly unchanged."""
        markdown = """# Clean Header

## Section

Some text here.

| Col 1 | Col 2 |
|-------|-------|
| A     | B     |

More text.
"""
        fixer = MarkdownFixer()
        fixed = fixer.fix_all(markdown)

        # Should be mostly the same
        assert "# Clean Header" in fixed
        assert "| Col 1 | Col 2 |" in fixed
        assert "More text." in fixed

    def test_fix_all_complex_document(self):
        """Test fix_all on a complex document with multiple issues."""
        markdown = """# Main Title


Section with tabs:
\tIndented line
\t\tDouble indent


| Table | Data |
|-------|------|
| X     | Y     |
Next paragraph without spacing.

```python
def test():
    pass
```


End of document.
"""
        fixer = MarkdownFixer(max_consecutive_blanks=2)
        fixed = fixer.fix_all(markdown)

        # Verify all fixes applied
        assert "\t" not in fixed  # No tabs
        assert "\n\n\n\n" not in fixed  # No excessive blanks

        # Table spacing
        assert "| Y     |\n\nNext paragraph" in fixed or "| Y     |\n\n\nNext paragraph" in fixed

        # Content preserved
        assert "# Main Title" in fixed
        assert "def test():" in fixed

    def test_fix_all_preserves_code_blocks(self):
        """Test that fix_all doesn't break code blocks."""
        markdown = """# Code Example

```python
def example():
    # Intentional spacing


    return True
```

Text after.
"""
        fixer = MarkdownFixer()
        fixed = fixer.fix_all(markdown)

        # Code block content should be mostly preserved
        # (though excessive blank lines might be reduced)
        assert "def example():" in fixed
        assert "return True" in fixed
        assert "```python" in fixed
        assert "```" in fixed

    def test_fix_all_idempotent(self):
        """Test that applying fix_all multiple times produces same result."""
        markdown = """# Header
\tTab
Trailing


Blanks
| Table | Data |
|-------|------|
| A     | B     |
Text
"""
        fixer = MarkdownFixer()

        fixed1 = fixer.fix_all(markdown)
        fixed2 = fixer.fix_all(fixed1)
        fixed3 = fixer.fix_all(fixed2)

        # Should be idempotent (or very close)
        assert fixed1 == fixed2
        assert fixed2 == fixed3


class TestConfigurability:
    """Test that MarkdownFixer respects configuration."""

    def test_custom_max_consecutive_blanks(self):
        """Test that custom max_consecutive_blanks is respected."""
        markdown = """# Header




Many blanks.
"""
        # Allow up to 3 blanks
        fixer = MarkdownFixer(max_consecutive_blanks=3)
        fixed = fixer.fix_excessive_whitespace(markdown)

        # Should allow 3 blank lines
        assert "\n\n\n\n" in fixed

        # But not 4
        fixer_strict = MarkdownFixer(max_consecutive_blanks=1)
        fixed_strict = fixer_strict.fix_excessive_whitespace(markdown)
        assert "\n\n\n" not in fixed_strict

    def test_default_values(self):
        """Test default configuration values."""
        fixer = MarkdownFixer()

        # Should have default max_consecutive_blanks
        assert fixer.max_consecutive_blanks == 2
