# Markdown Quality Assurance Strategy

This document outlines a comprehensive strategy for ensuring generated markdown documentation is both **content-valid** (current doc_validator) and **format-valid** (new formatting validators) before delivery to users.

---

## Problem Statement

**Current Situation:**
- ✅ We have `doc_validator.py` for **content validation** (clarity, maintenance, truth, value)
- ❌ We have **NO automated formatting validation** for:
  - Excessive whitespace (>2 consecutive blank lines)
  - Table formatting errors (misaligned separators, missing columns)
  - Malformed markdown syntax
  - GitHub/GitLab rendering issues

**Recent Evidence:**
- Table separator issues (missing conditional columns) - Issue #3
- Excessive blank lines (10-30+ extra lines) - Issue #1
- Inconsistent table row spacing - Issue #2

**User Impact:**
- Poor human readability
- Tables don't render on GitHub
- Documentation looks unprofessional
- Manual fixes required post-generation

---

## Proposed Solution: Multi-Layer QA Strategy

### **Layer 1: Template-Level Prevention** (Current - Just Implemented)
**Status:** ✅ Partially Complete

**What We Have:**
- Jinja2 whitespace control (`{%-` and `-%}`) in templates
- Fixed conditional table separators
- Consistent table row rendering

**Gaps:**
- No systematic checks during template development
- Easy to regress with future template changes
- No automated testing of template output

**Recommendation:**
- Add snapshot testing for templates
- Pre-commit hooks for template changes

---

### **Layer 2: Markdown Formatting Validator** (NEW - Priority 1)
**Status:** ❌ Not Implemented

Create `docsible/validators/markdown_validator.py` to check **raw markdown formatting** before writing to disk.

#### **2A: Whitespace Validation**

```python
# docsible/validators/markdown_validator.py
from typing import List, Tuple
from .doc_validator import ValidationIssue, ValidationSeverity, ValidationType

class MarkdownValidator:
    """Validates raw markdown formatting for human readability."""

    def validate_whitespace(self, markdown: str) -> List[ValidationIssue]:
        """Check for excessive whitespace issues."""
        issues = []
        lines = markdown.split('\n')

        # Check for excessive consecutive blank lines
        blank_count = 0
        max_blanks = 0
        blank_line_start = None

        for i, line in enumerate(lines, 1):
            if line.strip() == '':
                if blank_count == 0:
                    blank_line_start = i
                blank_count += 1
                max_blanks = max(max_blanks, blank_count)
            else:
                if blank_count > 2:  # More than 2 consecutive blank lines
                    issues.append(ValidationIssue(
                        type=ValidationType.CLARITY,
                        severity=ValidationSeverity.WARNING,
                        message=f"Excessive blank lines: {blank_count} consecutive empty lines",
                        line_number=blank_line_start,
                        suggestion=f"Reduce to maximum 2 blank lines for better readability"
                    ))
                blank_count = 0

        # Check for trailing whitespace
        trailing_lines = [i for i, line in enumerate(lines, 1) if line != line.rstrip()]
        if len(trailing_lines) > 10:
            issues.append(ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.INFO,
                message=f"Found {len(trailing_lines)} lines with trailing whitespace",
                suggestion="Remove trailing spaces for cleaner output"
            ))

        # Check for tab characters (should be spaces in markdown)
        tab_lines = [i for i, line in enumerate(lines, 1) if '\t' in line]
        if tab_lines:
            issues.append(ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.WARNING,
                message=f"Found tab characters on {len(tab_lines)} lines",
                line_number=tab_lines[0] if tab_lines else None,
                suggestion="Replace tabs with spaces for consistent rendering"
            ))

        return issues

    def validate_tables(self, markdown: str) -> List[ValidationIssue]:
        """Validate markdown table formatting."""
        issues = []
        lines = markdown.split('\n')

        in_table = False
        table_start = None
        table_lines = []
        separator_line = None
        header_line = None

        for i, line in enumerate(lines, 1):
            if line.strip().startswith('|') and line.strip().endswith('|'):
                if not in_table:
                    in_table = True
                    table_start = i
                    table_lines = []
                    separator_line = None
                    header_line = None

                table_lines.append((i, line))

                # Detect separator row (contains only |, -, and spaces)
                if re.match(r'^\s*\|[\s\-|:]+\|\s*$', line):
                    separator_line = (i, line)
                    if table_lines:
                        header_line = table_lines[-2] if len(table_lines) >= 2 else None
            else:
                if in_table:
                    # End of table - validate it
                    issues.extend(self._validate_single_table(
                        table_lines, header_line, separator_line, table_start
                    ))
                    in_table = False

        # Validate last table if file ends with table
        if in_table:
            issues.extend(self._validate_single_table(
                table_lines, header_line, separator_line, table_start
            ))

        return issues

    def _validate_single_table(
        self,
        table_lines: List[Tuple[int, str]],
        header_line: Optional[Tuple[int, str]],
        separator_line: Optional[Tuple[int, str]],
        table_start: int
    ) -> List[ValidationIssue]:
        """Validate a single markdown table."""
        issues = []

        if not header_line or not separator_line:
            issues.append(ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.ERROR,
                message="Malformed table: missing header or separator row",
                line_number=table_start,
                suggestion="Ensure table has header row followed by separator row (|---|---|)"
            ))
            return issues

        # Count columns in header
        header_text = header_line[1]
        header_cols = len([c for c in header_text.split('|') if c.strip()])

        # Count separators
        sep_text = separator_line[1]
        sep_cols = len([c for c in sep_text.split('|') if c.strip() and '-' in c])

        # Check column count mismatch
        if header_cols != sep_cols:
            issues.append(ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.ERROR,
                message=f"Table column mismatch: header has {header_cols} columns, separator has {sep_cols}",
                line_number=separator_line[0],
                suggestion=f"Add {abs(header_cols - sep_cols)} separator(s) to match header columns"
            ))

        # Check data rows have correct column count
        for line_num, line_text in table_lines[2:]:  # Skip header and separator
            if re.match(r'^\s*\|[\s\-|:]+\|\s*$', line_text):
                continue  # Skip if it's another separator

            data_cols = len([c for c in line_text.split('|') if c.strip() or c == ''])
            # Account for leading/trailing pipes
            actual_cols = data_cols - 2 if line_text.strip().startswith('|') and line_text.strip().endswith('|') else data_cols

            if actual_cols != header_cols and actual_cols != sep_cols:
                issues.append(ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.WARNING,
                    message=f"Row has {actual_cols} columns, expected {header_cols}",
                    line_number=line_num,
                    suggestion="Ensure all table rows have the same number of columns"
                ))

        return issues

    def validate_syntax(self, markdown: str) -> List[ValidationIssue]:
        """Validate markdown syntax basics."""
        issues = []
        lines = markdown.split('\n')

        # Check for unclosed code blocks
        code_block_count = sum(1 for line in lines if line.strip().startswith('```'))
        if code_block_count % 2 != 0:
            issues.append(ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.ERROR,
                message=f"Unclosed code block: found {code_block_count} code fence markers (should be even)",
                suggestion="Ensure every ``` has a closing ```"
            ))

        # Check for unclosed HTML details tags
        details_open = sum(1 for line in lines if '<details>' in line.lower())
        details_close = sum(1 for line in lines if '</details>' in line.lower())
        if details_open != details_close:
            issues.append(ValidationIssue(
                type=ValidationType.CLARITY,
                severity=ValidationSeverity.ERROR,
                message=f"Unclosed <details> tag: {details_open} open, {details_close} close",
                suggestion="Ensure every <details> has matching </details>"
            ))

        # Check for proper heading hierarchy (no skipping levels)
        heading_levels = []
        for i, line in enumerate(lines, 1):
            match = re.match(r'^(#{1,6})\s+', line)
            if match:
                level = len(match.group(1))
                heading_levels.append((i, level))

        for i in range(1, len(heading_levels)):
            prev_line, prev_level = heading_levels[i-1]
            curr_line, curr_level = heading_levels[i]

            # Check if we jumped more than one level
            if curr_level > prev_level + 1:
                issues.append(ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.INFO,
                    message=f"Heading hierarchy skip: jumped from h{prev_level} to h{curr_level}",
                    line_number=curr_line,
                    suggestion=f"Consider using h{prev_level + 1} instead of h{curr_level}"
                ))

        return issues

    def validate(self, markdown: str) -> List[ValidationIssue]:
        """Run all markdown formatting validations."""
        issues = []
        issues.extend(self.validate_whitespace(markdown))
        issues.extend(self.validate_tables(markdown))
        issues.extend(self.validate_syntax(markdown))
        return issues
```

**Integration Point:**

```python
# In readme_renderer.py, before writing file
def render_role(self, ...) -> str:
    # ... existing rendering logic ...
    rendered_markdown = template.render(...)

    # NEW: Validate markdown formatting
    from docsible.validators.markdown_validator import MarkdownValidator

    markdown_validator = MarkdownValidator()
    formatting_issues = markdown_validator.validate(rendered_markdown)

    # Log warnings but don't fail (yet)
    for issue in formatting_issues:
        if issue.severity == ValidationSeverity.ERROR:
            logger.error(f"Markdown formatting error at line {issue.line_number}: {issue.message}")
        elif issue.severity == ValidationSeverity.WARNING:
            logger.warning(f"Markdown formatting warning at line {issue.line_number}: {issue.message}")

    # Optionally auto-fix some issues
    if self.auto_fix_formatting:
        rendered_markdown = self._fix_markdown_formatting(rendered_markdown, formatting_issues)

    return rendered_markdown
```

---

### **Layer 3: Markdown Linter Integration** (NEW - Priority 2)
**Status:** ❌ Not Implemented

Use industry-standard markdown linters as additional validation layer.

#### **3A: markdownlint-cli Integration**

```python
# docsible/validators/external_linters.py
import subprocess
import json
from typing import List, Optional

def run_markdownlint(markdown_content: str, config: Optional[dict] = None) -> List[ValidationIssue]:
    """Run markdownlint-cli on markdown content."""
    try:
        # Write markdown to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(markdown_content)
            temp_file = f.name

        # Run markdownlint
        result = subprocess.run(
            ['markdownlint', '--json', temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Parse JSON output
        if result.stdout:
            lint_results = json.loads(result.stdout)
            issues = []

            for file_path, file_issues in lint_results.items():
                for issue in file_issues:
                    issues.append(ValidationIssue(
                        type=ValidationType.CLARITY,
                        severity=ValidationSeverity.WARNING,
                        message=f"{issue['ruleNames'][0]}: {issue['ruleDescription']}",
                        line_number=issue['lineNumber'],
                        suggestion=issue.get('errorDetail', '')
                    ))

            return issues

    except FileNotFoundError:
        logger.info("markdownlint not installed - skipping external linting")
        return []
    except Exception as e:
        logger.warning(f"markdownlint failed: {e}")
        return []

    finally:
        # Clean up temp file
        if 'temp_file' in locals():
            Path(temp_file).unlink(missing_ok=True)

    return []
```

**Configuration (.markdownlint.json):**

```json
{
  "default": true,
  "MD013": {
    "line_length": 120,
    "code_blocks": false,
    "tables": false
  },
  "MD033": false,
  "MD041": false,
  "MD012": {
    "maximum": 2
  }
}
```

---

### **Layer 4: Rendering Validation** (NEW - Priority 3)
**Status:** ❌ Not Implemented

Test how markdown actually renders on target platforms (GitHub, GitLab).

#### **4A: GitHub Markdown Rendering Test**

```python
# docsible/validators/rendering_validator.py
import requests
from typing import Optional

def validate_github_rendering(markdown: str) -> List[ValidationIssue]:
    """Test if markdown renders correctly on GitHub."""
    issues = []

    try:
        # Use GitHub Markdown API to test rendering
        response = requests.post(
            'https://api.github.com/markdown',
            json={'text': markdown, 'mode': 'markdown'},
            headers={'Accept': 'application/vnd.github.v3+json'},
            timeout=10
        )

        if response.status_code == 200:
            rendered_html = response.text

            # Check for common rendering issues
            if '<table>' not in rendered_html and '|' in markdown:
                issues.append(ValidationIssue(
                    type=ValidationType.VALUE,
                    severity=ValidationSeverity.ERROR,
                    message="Tables failed to render on GitHub",
                    suggestion="Check table formatting - separator row may be malformed"
                ))

            # Check for failed Mermaid diagrams
            if '```mermaid' in markdown:
                # GitHub renders mermaid in class="language-mermaid"
                if 'language-mermaid' not in rendered_html:
                    issues.append(ValidationIssue(
                        type=ValidationType.VALUE,
                        severity=ValidationSeverity.WARNING,
                        message="Mermaid diagrams may not render on GitHub",
                        suggestion="Verify mermaid syntax or consider exporting to SVG"
                    ))

    except Exception as e:
        logger.debug(f"GitHub rendering validation skipped: {e}")

    return issues
```

**Note:** This requires network access, so make it **optional** (opt-in via `--validate-rendering` flag).

---

### **Layer 5: Auto-Fix Capabilities** (NEW - Priority 3)
**Status:** ❌ Not Implemented

Automatically fix common formatting issues.

```python
# docsible/validators/markdown_fixer.py
class MarkdownFixer:
    """Automatically fix common markdown formatting issues."""

    def fix_excessive_whitespace(self, markdown: str) -> str:
        """Remove excessive blank lines (max 2 consecutive)."""
        lines = markdown.split('\n')
        fixed_lines = []
        blank_count = 0

        for line in lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:  # Allow max 2 consecutive
                    fixed_lines.append(line)
            else:
                blank_count = 0
                fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_trailing_whitespace(self, markdown: str) -> str:
        """Remove trailing whitespace from all lines."""
        return '\n'.join(line.rstrip() for line in markdown.split('\n'))

    def fix_table_spacing(self, markdown: str) -> str:
        """Ensure proper spacing around tables."""
        lines = markdown.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            # Add blank line before table if missing
            if line.strip().startswith('|') and i > 0:
                prev_line = lines[i-1].strip()
                if prev_line and not prev_line.startswith('|'):
                    if i > 0 and lines[i-1].strip() != '':
                        fixed_lines.append('')  # Add blank line

            fixed_lines.append(line)

            # Add blank line after table if missing
            if line.strip().startswith('|') and i < len(lines) - 1:
                next_line = lines[i+1].strip() if i+1 < len(lines) else ''
                if next_line and not next_line.startswith('|'):
                    if i < len(lines) - 1 and lines[i+1].strip() != '':
                        fixed_lines.append('')  # Add blank line

        return '\n'.join(fixed_lines)

    def fix_all(self, markdown: str) -> str:
        """Apply all auto-fixes."""
        markdown = self.fix_trailing_whitespace(markdown)
        markdown = self.fix_excessive_whitespace(markdown)
        markdown = self.fix_table_spacing(markdown)
        return markdown
```

---

### **Layer 6: Pre-delivery Quality Gate** (NEW - Priority 1)
**Status:** ❌ Not Implemented

Add final validation before writing README.md.

```python
# In readme_renderer.py
def write_readme(self, content: str, output_path: Path, validate: bool = True):
    """Write README with optional validation gate."""

    if validate:
        # Run all validations
        validation_results = self._validate_output(content)

        # Check for errors
        if validation_results['has_errors']:
            errors = validation_results['errors']
            logger.error(f"README validation failed with {len(errors)} errors:")
            for error in errors:
                logger.error(f"  Line {error.line_number}: {error.message}")

            if not self.force_write:
                raise ValidationError(
                    f"Generated README has {len(errors)} formatting errors. "
                    f"Fix templates or use --force to write anyway."
                )

        # Log warnings
        warnings = validation_results['warnings']
        if warnings:
            logger.warning(f"README has {len(warnings)} formatting warnings:")
            for warning in warnings[:5]:  # Show first 5
                logger.warning(f"  Line {warning.line_number}: {warning.message}")

    # Write to file
    output_path.write_text(content)
    logger.info(f"✓ README written to {output_path}")
```

**CLI Integration:**

```python
# New flags in options/output.py
f = click.option(
    "--validate/--no-validate",
    default=True,
    help="Validate markdown formatting before writing (default: enabled)"
)(f)

f = click.option(
    "--strict-validation",
    is_flag=True,
    help="Fail generation if validation errors found (instead of just warning)"
)(f)

f = click.option(
    "--auto-fix",
    is_flag=True,
    help="Automatically fix common formatting issues before writing"
)(f)
```

---

## Recommended Implementation Plan

### **Phase 1: Critical Fixes (Week 1)**
**Goal:** Catch the issues we just manually fixed

1. ✅ Implement `MarkdownValidator.validate_whitespace()`
2. ✅ Implement `MarkdownValidator.validate_tables()`
3. ✅ Integrate into `readme_renderer.py` (warning mode)
4. ✅ Add basic auto-fixer for whitespace
5. ✅ Add `--validate` and `--auto-fix` CLI flags

**Deliverable:** Prevents Issues #1, #2, #3 from happening again

---

### **Phase 2: Enhanced Validation (Week 2-3)**
**Goal:** Comprehensive quality assurance

6. ✅ Implement `MarkdownValidator.validate_syntax()`
7. ✅ Add markdownlint integration (optional, graceful fallback)
8. ✅ Add `--strict-validation` flag
9. ✅ Create validation report in output
10. ✅ Add regression tests with snapshot testing

**Deliverable:** Production-quality markdown output

---

### **Phase 3: Advanced Features (Week 4+)**
**Goal:** Best-in-class quality

11. ✅ GitHub rendering validation (opt-in)
12. ✅ Interactive fix mode (show issues, ask user to fix)
13. ✅ Validation metrics in complexity report
14. ✅ Pre-commit hooks for template validation

**Deliverable:** Industry-leading documentation quality

---

## Testing Strategy

### **Regression Test Suite**

```python
# tests/test_markdown_validation.py
def test_excessive_whitespace_detected():
    """Test that excessive blank lines are detected."""
    markdown = """
# Header

Some text




More text
"""
    validator = MarkdownValidator()
    issues = validator.validate_whitespace(markdown)

    # Should detect >2 consecutive blank lines
    assert any('excessive blank lines' in issue.message.lower() for issue in issues)

def test_table_column_mismatch_detected():
    """Test that table column mismatches are detected."""
    markdown = """
| Header 1 | Header 2 | Header 3 |
|----------|----------|
| Data 1   | Data 2   | Data 3   |
"""
    validator = MarkdownValidator()
    issues = validator.validate_tables(markdown)

    # Should detect 3 header columns vs 2 separators
    assert any('column mismatch' in issue.message.lower() for issue in issues)

def test_autofix_whitespace():
    """Test that excessive whitespace is automatically fixed."""
    markdown = "Line 1\n\n\n\n\nLine 2"
    fixer = MarkdownFixer()
    fixed = fixer.fix_excessive_whitespace(markdown)

    # Should reduce to max 2 blank lines
    assert fixed == "Line 1\n\n\nLine 2"
```

### **Snapshot Testing for Templates**

```python
# tests/snapshots/test_template_output.py
def test_hybrid_template_formatting(snapshot):
    """Ensure hybrid template produces correctly formatted markdown."""
    role_info = load_test_role('complex_role')
    renderer = ReadmeRenderer(template='hybrid_modular')

    output = renderer.render_role(role_info)

    # Validate formatting
    validator = MarkdownValidator()
    issues = validator.validate(output)

    # Should have no formatting errors
    errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
    assert len(errors) == 0, f"Template produced formatting errors: {errors}"

    # Snapshot test - catch unexpected changes
    snapshot.assert_match(output, 'hybrid_template_output.md')
```

---

## Configuration

Add validation settings to `.docsible.yml`:

```yaml
validation:
  # Enable markdown formatting validation
  enabled: true

  # Fail generation if errors found (vs. warning only)
  strict: false

  # Auto-fix common issues
  auto_fix: true

  # External linters (requires installation)
  use_markdownlint: false

  # GitHub rendering check (requires network)
  check_rendering: false

  # Rules to check
  rules:
    max_consecutive_blanks: 2
    max_line_length: 120
    require_table_separators: true
    check_heading_hierarchy: true
    check_unclosed_tags: true

  # Auto-fix options
  auto_fix_options:
    trailing_whitespace: true
    excessive_blanks: true
    table_spacing: true
```

---

## CLI Output Examples

### **With Validation Enabled (Default):**

```bash
$ docsible role --role ./my-role --graph

📝 Generating documentation...
✓ Analyzed role complexity: MEDIUM (18 tasks)
✓ Generated sequence diagram
✓ Generated dependency matrix
✓ Rendered README.md

⚠️  Validation warnings (3):
  Line 42: Excessive blank lines: 4 consecutive empty lines
  Line 89: Table column mismatch: header has 5 columns, separator has 4
  Line 156: Heading hierarchy skip: jumped from h2 to h4

ℹ️  Run with --auto-fix to automatically correct these issues

✓ README.md written successfully
```

### **With Auto-Fix:**

```bash
$ docsible role --role ./my-role --graph --auto-fix

📝 Generating documentation...
✓ Analyzed role complexity: MEDIUM (18 tasks)
✓ Generated sequence diagram
✓ Generated dependency matrix
✓ Rendered README.md

🔧 Auto-fixed formatting issues (3):
  ✓ Reduced excessive blank lines
  ✓ Fixed table column separators
  ✓ Removed trailing whitespace

✓ README.md written successfully with no validation errors
```

### **With Strict Validation:**

```bash
$ docsible role --role ./my-role --strict-validation

📝 Generating documentation...
✓ Analyzed role complexity: MEDIUM (18 tasks)
✓ Generated sequence diagram
✓ Rendered README.md

❌ Validation FAILED with 2 errors:
  Line 89: Table column mismatch: header has 5 columns, separator has 4
  Line 120: Unclosed code block: found 3 code fence markers

Generation aborted. Fix template issues or use --no-validate to skip.
```

---

## Integration with Existing doc_validator

```python
# Unified validation flow
class QualityAssurance:
    """Unified quality assurance for generated documentation."""

    def __init__(self):
        self.content_validator = DocumentationValidator()  # Existing
        self.markdown_validator = MarkdownValidator()      # New
        self.markdown_fixer = MarkdownFixer()              # New

    def validate_and_fix(
        self,
        markdown: str,
        role_info: Dict,
        complexity_report: Any,
        auto_fix: bool = True
    ) -> Tuple[str, ValidationResult]:
        """
        Run all validations and optionally auto-fix issues.

        Returns:
            (fixed_markdown, validation_result)
        """
        # Step 1: Auto-fix formatting if enabled
        if auto_fix:
            markdown = self.markdown_fixer.fix_all(markdown)

        # Step 2: Validate markdown formatting
        formatting_issues = self.markdown_validator.validate(markdown)

        # Step 3: Validate content quality
        content_result = self.content_validator.validate(
            markdown, role_info, complexity_report
        )

        # Step 4: Combine results
        all_issues = formatting_issues + content_result.issues

        final_result = ValidationResult(
            passed=not any(i.severity == ValidationSeverity.ERROR for i in all_issues),
            score=content_result.score,  # Keep content score
            issues=all_issues,
            metrics={
                'content': content_result.metrics,
                'formatting': {
                    'total_issues': len(formatting_issues),
                    'errors': len([i for i in formatting_issues if i.severity == ValidationSeverity.ERROR]),
                    'warnings': len([i for i in formatting_issues if i.severity == ValidationSeverity.WARNING]),
                }
            }
        )

        return markdown, final_result
```

---

## Benefits

### **For Users:**
- ✅ **Cleaner markdown** - No more excessive whitespace
- ✅ **Working tables** - Guaranteed to render on GitHub/GitLab
- ✅ **Professional output** - Consistent, readable documentation
- ✅ **Fewer manual fixes** - Auto-fix handles common issues

### **For Developers:**
- ✅ **Catch issues early** - Before users report them
- ✅ **Template quality enforcement** - Can't merge broken templates
- ✅ **Regression prevention** - Snapshot tests catch changes
- ✅ **Faster debugging** - Clear validation messages

### **For Docsible Project:**
- ✅ **Higher quality** - Industry-leading documentation output
- ✅ **Better reputation** - Users trust the output
- ✅ **Less support burden** - Fewer formatting bug reports
- ✅ **Confidence in changes** - Safe to modify templates

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| False positives (valid markdown flagged as error) | Medium | Make strict mode opt-in; allow config overrides |
| Performance impact (extra validation time) | Low | Make validation optional (`--no-validate`); optimize validators |
| External dependency (markdownlint) | Low | Graceful fallback; make optional |
| Breaking changes (rejecting previously valid output) | Medium | Phased rollout; warnings before errors |

---

## Success Metrics

**After Phase 1 (Week 1):**
- 0 table formatting errors in generated READMEs
- <2 consecutive blank lines in all outputs
- 100% of templates pass validation

**After Phase 2 (Week 3):**
- 95% of generated READMEs score >90 on validation
- <5% of users use `--no-validate` flag
- 0 user-reported formatting bugs

**After Phase 3 (Week 6):**
- 100% GitHub rendering compatibility
- Markdown quality score visible in output
- Pre-commit hooks prevent template regressions

---

## Next Steps

1. **Decision:** Approve implementation plan
2. **Phase 1 Implementation:** `MarkdownValidator` + basic auto-fix (1 week)
3. **Testing:** Create regression test suite
4. **Documentation:** Update user docs with validation flags
5. **Release:** Ship as opt-in initially, default in next major version

---

*Document created: 2025-12-11*
*Priority: HIGH - Prevents quality issues from reaching users*
*Estimated effort: 3 weeks (phased implementation)*
