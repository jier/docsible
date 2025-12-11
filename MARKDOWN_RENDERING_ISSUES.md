# Markdown Rendering Issues Analysis

This document explains the three main rendering issues in Docsible's generated markdown and their root causes.

---

## Issue 1: Big White Spaces in Generated Markdown

### Root Cause
Multiple blank lines accumulate throughout template files due to lack of Jinja2 whitespace control.

### Examples

#### `complexity_analysis.jinja2` (Lines with extra whitespace)
```jinja2
| Task Includes | {{ complexity_report.metrics.task_includes | escape_table_cell }} |
                          ← BLANK LINE 19
{% if complexity_report.integration_points %}
```

```jinja2
{% if integration.uses_credentials %}- **⚠️ Requires Credentials**{% endif %}
                          ← BLANK LINE 30 (inside loop - multiplies!)
{% endfor %}
```

```jinja2
{% endfor %}
                          ← BLANK LINE 32
{% endif %}
                          ← BLANK LINE 33
```

#### `dependency_matrix.jinja2` (Similar pattern)
```jinja2
## Task Dependency Matrix
                          ← BLANK LINE 4
*This role has {{ complexity_report.metrics.total_tasks }} tasks...*
                          ← BLANK LINE 6
{{ dependency_matrix }}
                          ← BLANK LINE 8
### How to Use This Table
```

#### `defaults_hybrid.jinja2`
```jinja2
{% endif %}
                          ← BLANK LINE 11 at end of file
```

### Why This Happens
Jinja2 preserves all whitespace (including blank lines) unless you use whitespace control:
- `{%-` removes whitespace BEFORE the tag
- `-%}` removes whitespace AFTER the tag

Without these controls, every blank line in the template becomes a blank line in the output.

### Impact
- Multiple sections each adding 2-5 blank lines = 10-30 extra blank lines total
- Creates visually jarring "big white spaces" in rendered markdown
- Inconsistent spacing between sections

### Solution
Add whitespace control to templates:

```jinja2
{# BEFORE #}
| Task Includes | {{ value }} |

{% if condition %}

{# AFTER #}
| Task Includes | {{ value }} |
{%- if condition %}
```

---

## Issue 2: Table Rows Not Correctly Indented

### Root Cause
Inconsistent whitespace control between header generation and row generation in table macros.

### Example: `table_hybrid.jinja2`

```jinja2
{% macro render_table(file_data, file_path, role) -%}
| Variable | Default Value | Type | Description |
|----------|---------------|------|-------------|
{%- for key, details in file_data.items() %}
{{ render_row(key, details, file_path, role) }}
{%- endfor %}
{%- endmacro %}

{% macro render_row(key, details, file_path, role) -%}
| `{{ key }}` | {{ value }} | {{ type }} | {{ description }} |
{%- endmacro %}
```

**The Problem:**
1. Line 3 uses `{%- for` (strips whitespace before)
2. Line 4 calls `{{ render_row(...) }}` WITHOUT `-` on right side
3. The `render_row` macro (line 9) outputs a table row
4. Line 5 uses `{%- endfor %}` (strips whitespace before)

**What Happens:**
```markdown
| Variable | Default Value | Type | Description |
|----------|---------------|------|-------------|
| `var1` | value1 | str | desc1 |
                                   ← Extra newline from line 10 endmacro
| `var2` | value2 | int | desc2 |
                                   ← Extra newline
| `var3` | value3 | bool | desc3 |
```

The newline after each `{%- endmacro %}` in `render_row` is preserved, creating visual gaps between rows.

### Why Standard vs Hybrid Differs

**`table_standard.jinja2` (Better formatted):**
```jinja2
{%- for key, details in file_data.items() -%}
{{ render_row(key, details, file_path, role, columns) }}
{%- endfor -%}
```
Uses `{%- ... -%}` on BOTH sides = tighter control

**`table_hybrid.jinja2` (Inconsistent):**
```jinja2
{%- for key, details in file_data.items() %}
{{ render_row(key, details, file_path, role) }}
{%- endfor %}
```
Missing `-%}` on line 1 = whitespace leak

### Impact
- Table rows have inconsistent spacing
- Hybrid templates look "messier" than standard templates
- Some tables are clean, others have gaps between rows

### Solution
Add consistent whitespace control:

```jinja2
{# BEFORE #}
{%- for key, details in file_data.items() %}
{{ render_row(key, details, file_path, role) }}
{%- endfor %}

{# AFTER #}
{%- for key, details in file_data.items() -%}
{{ render_row(key, details, file_path, role) }}
{%- endfor -%}
```

OR simplify the macro call:

```jinja2
{%- for key, details in file_data.items() -%}
| `{{ key }}` | {{ value }} | {{ type }} | {{ description }} |
{%- endfor -%}
```

---

## Issue 3: Table Fields Always Generated (Not Conditional)

### Root Cause
Missing column separators in conditional table headers.

### Example: `table_standard.jinja2` (Line 8-9)

```jinja2
{% macro render_header(columns) %}
| Var | Type | Value |{% if columns.has_choices %} Choices |{% endif %}{%- if columns.has_required %} Required |{% endif %}{%- if columns.has_title %} Title |{% endif %}
|-----|------|-------|
{%- endmacro %}
```

**The Problem:**
- Line 8: Header row adds conditional columns (Choices, Required, Title)
- Line 9: Separator row has FIXED 3 columns only!
- Missing: `{% if columns.has_choices %}------|{% endif %}` for each conditional column

**Visual Result:**
```markdown
| Var | Type | Value | Choices | Required |
|-----|------|-------|                        ← Missing separators!

| var1 | str | foo | yes | true |           ← Table breaks visually
```

### Why This Happens
The template author added conditional headers but forgot to add matching conditional separators in the separator row.

### Impact
- Markdown tables render incorrectly when conditional columns are present
- Column alignment breaks
- Some markdown renderers show malformed tables
- Inconsistent table widths

### Solution

**Fix the separator row to match headers:**

```jinja2
{% macro render_header(columns) %}
| Var | Type | Value |{% if columns.has_choices %} Choices |{% endif %}{%- if columns.has_required %} Required |{% endif %}{%- if columns.has_title %} Title |{% endif %}
|-----|------|-------|{% if columns.has_choices %}---------|{% endif %}{%- if columns.has_required %}----------|{% endif %}{%- if columns.has_title %}-------|{% endif %}
{%- endmacro %}
```

---

## Summary Table

| Issue | File(s) Affected | Root Cause | Severity |
|-------|------------------|------------|----------|
| **Big White Spaces** | `complexity_analysis.jinja2`<br>`dependency_matrix.jinja2`<br>`defaults_hybrid.jinja2`<br>Most section templates | Missing `{%-` and `-%}` whitespace control | Medium |
| **Inconsistent Row Indentation** | `table_hybrid.jinja2`<br>`table_standard.jinja2` | Incomplete whitespace control in for loops and macros | Low-Medium |
| **Missing Table Separators** | `table_standard.jinja2` | Conditional headers without conditional separators | High |

---

## Recommended Fix Priority

1. **High**: Fix Issue 3 (table separators) - breaks rendering
2. **Medium**: Fix Issue 1 (whitespace) - affects all generated docs
3. **Low-Medium**: Fix Issue 2 (row indentation) - cosmetic but inconsistent

---

## Jinja2 Whitespace Control Reference

```jinja2
{# Strip whitespace BEFORE tag #}
{%- if condition %}

{# Strip whitespace AFTER tag #}
{% if condition -%}

{# Strip on BOTH sides #}
{%- if condition -%}

{# Apply to all control structures #}
{%- for item in items -%}
{%- if condition -%}
{%- endif -%}
{%- endfor -%}
```

**Best Practice:** Use `{%- ... -%}` consistently on ALL control structures to prevent whitespace accumulation.

---

## Testing Methodology

To verify these issues:

1. Generate documentation: `docsible role --role . --complexity-report --show-dependencies`
2. Count blank lines: `grep -c "^$" README.md`
3. Inspect table structure with markdown linter
4. Compare hybrid vs standard template outputs side-by-side

---

*Analysis generated: 2025-12-11*
