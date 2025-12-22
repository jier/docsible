# Migration Guide: Old API → RenderContext

This guide helps you migrate from the old parameter-heavy API to the new clean `RenderContext` API.

## Why Migrate?

The old `render_role()` API has **25 parameters**, making it:
- ❌ Hard to read and understand
- ❌ Error-prone (easy to mix up parameter order)
- ❌ Difficult to maintain and extend

The new `RenderContext` API:
- ✅ Only 2 parameters (context + output_path)
- ✅ Self-documenting with Pydantic validation
- ✅ Type-safe and IDE-friendly
- ✅ Easy to extend without breaking changes

## Quick Comparison

### Old API (Still Works, But Verbose)
```python
from docsible.renderers import ReadmeRenderer
from pathlib import Path

renderer = ReadmeRenderer()
renderer.render_role(
    role_info=role_data,
    output_path=Path('README.md'),
    template_type='hybrid',
    custom_template_path=None,
    mermaid_code_per_file=diagrams,
    sequence_diagram_high_level=seq_high,
    sequence_diagram_detailed=seq_detail,
    state_diagram=state,
    integration_boundary_diagram=boundary,
    architecture_diagram=arch,
    complexity_report=complexity,
    include_complexity=True,
    dependency_matrix=matrix,
    dependency_summary=summary,
    show_dependency_matrix=True,
    no_vars=False,
    no_tasks=False,
    no_diagrams=False,
    simplify_diagrams=False,
    no_examples=False,
    no_metadata=False,
    no_handlers=False,
    append=False
)  # 25 parameters!
```

### New API (Recommended)
```python
from docsible.renderers import ReadmeRenderer, RenderContext
from pathlib import Path

renderer = ReadmeRenderer()
context = RenderContext(
    role_info=role_data,
    template_type='hybrid',
    mermaid_code_per_file=diagrams,
    sequence_diagram_high_level=seq_high,
    sequence_diagram_detailed=seq_detail,
    state_diagram=state,
    integration_boundary_diagram=boundary,
    architecture_diagram=arch,
    complexity_report=complexity,
    include_complexity=True,
    dependency_matrix=matrix,
    dependency_summary=summary,
    show_dependency_matrix=True
    # Only specify what you need - rest uses sensible defaults
)
renderer.render_role_from_context(context, Path('README.md'))  # 2 parameters!
```

## Step-by-Step Migration

### Step 1: Import RenderContext

**Before:**
```python
from docsible.renderers import ReadmeRenderer
```

**After:**
```python
from docsible.renderers import ReadmeRenderer, RenderContext
```

### Step 2: Create RenderContext Instead of Passing Parameters

**Before:**
```python
renderer.render_role(
    role_info=role_data,
    output_path=Path('README.md'),
    template_type='hybrid',
    no_vars=False,
    no_diagrams=False
)
```

**After:**
```python
context = RenderContext(
    role_info=role_data,
    template_type='hybrid',
    no_vars=False,
    no_diagrams=False
)
renderer.render_role_from_context(context, Path('README.md'))
```

### Step 3: Use Default Values

One major benefit: you only specify what you need!

**Before:**
```python
renderer.render_role(
    role_info=role_data,
    output_path=Path('README.md'),
    template_type='standard',  # default
    custom_template_path=None,  # default
    mermaid_code_per_file=None,  # default
    # ... 20 more default parameters
)
```

**After:**
```python
context = RenderContext(role_info=role_data)  # All defaults!
renderer.render_role_from_context(context, Path('README.md'))
```

## Common Patterns

### Pattern 1: Simple Role (No Diagrams)

**Before:**
```python
renderer.render_role(
    role_info={'name': 'my_role', 'description': 'Simple role'},
    output_path=Path('README.md'),
    template_type='standard',
    no_diagrams=True,
    no_examples=True
)
```

**After:**
```python
context = RenderContext(
    role_info={'name': 'my_role', 'description': 'Simple role'},
    no_diagrams=True,
    no_examples=True
)
renderer.render_role_from_context(context, Path('README.md'))
```

### Pattern 2: Complex Role With All Diagrams

**Before:**
```python
renderer.render_role(
    role_info=complex_role_data,
    output_path=Path('README.md'),
    template_type='hybrid',
    mermaid_code_per_file=task_diagrams,
    sequence_diagram_high_level=seq_diagram,
    architecture_diagram=arch_diagram,
    complexity_report=complexity_analysis,
    include_complexity=True
)
```

**After:**
```python
context = RenderContext(
    role_info=complex_role_data,
    template_type='hybrid',
    mermaid_code_per_file=task_diagrams,
    sequence_diagram_high_level=seq_diagram,
    architecture_diagram=arch_diagram,
    complexity_report=complexity_analysis,
    include_complexity=True
)
renderer.render_role_from_context(context, Path('README.md'))
```

### Pattern 3: Minimal Output (Documentation Only)

**Before:**
```python
renderer.render_role(
    role_info=role_data,
    output_path=Path('README.md'),
    no_vars=True,
    no_tasks=True,
    no_diagrams=True,
    no_examples=True,
    no_metadata=True,
    no_handlers=True
)
```

**After:**
```python
context = RenderContext(
    role_info=role_data,
    no_vars=True,
    no_tasks=True,
    no_diagrams=True,
    no_examples=True,
    no_metadata=True,
    no_handlers=True
)
renderer.render_role_from_context(context, Path('README.md'))
```

### Pattern 4: Custom Template

**Before:**
```python
renderer.render_role(
    role_info=role_data,
    output_path=Path('README.md'),
    template_type='standard',
    custom_template_path='/path/to/custom.jinja2'
)
```

**After:**
```python
context = RenderContext(
    role_info=role_data,
    custom_template_path='/path/to/custom.jinja2'
)
renderer.render_role_from_context(context, Path('README.md'))
```

## Advanced: Pydantic Benefits

RenderContext is a Pydantic model, giving you extra features:

### 1. Validation
```python
from pydantic import ValidationError

try:
    context = RenderContext()  # Missing required role_info!
except ValidationError as e:
    print(e)  # Clear error message
```

### 2. Serialization
```python
context = RenderContext(role_info={'name': 'test'})

# To dictionary
data = context.model_dump()

# To JSON
json_str = context.model_dump_json()

# From dictionary
context2 = RenderContext(**data)
```

### 3. IDE Autocomplete
RenderContext provides full IDE autocomplete and type hints, making development faster and less error-prone.

## Parameter Mapping Reference

| Old Parameter | RenderContext Field |
|---------------|---------------------|
| `role_info` | `role_info` (required) |
| `template_type` | `template_type` |
| `custom_template_path` | `custom_template_path` |
| `mermaid_code_per_file` | `mermaid_code_per_file` |
| `sequence_diagram_high_level` | `sequence_diagram_high_level` |
| `sequence_diagram_detailed` | `sequence_diagram_detailed` |
| `state_diagram` | `state_diagram` |
| `integration_boundary_diagram` | `integration_boundary_diagram` |
| `architecture_diagram` | `architecture_diagram` |
| `complexity_report` | `complexity_report` |
| `include_complexity` | `include_complexity` |
| `dependency_matrix` | `dependency_matrix` |
| `dependency_summary` | `dependency_summary` |
| `show_dependency_matrix` | `show_dependency_matrix` |
| `no_vars` | `no_vars` |
| `no_tasks` | `no_tasks` |
| `no_diagrams` | `no_diagrams` |
| `simplify_diagrams` | `simplify_diagrams` |
| `no_examples` | `no_examples` |
| `no_metadata` | `no_metadata` |
| `no_handlers` | `no_handlers` |
| `append` | `append` |

Note: `output_path` is now passed separately to `render_role_from_context()` instead of being in the context.

## Backward Compatibility

**The old API still works!** You can migrate at your own pace:

```python
# Old API - still supported
renderer.render_role(role_info=data, output_path=path, ...)

# New API - recommended for new code
renderer.render_role_from_context(context, path)
```

Both methods will be supported for the foreseeable future.

## FAQ

**Q: Why keep `output_path` separate from RenderContext?**  
A: `output_path` is about *where* to write, while RenderContext is about *what* to write. Separating them makes the API clearer and allows reusing the same context for multiple outputs.

**Q: Can I modify a RenderContext after creating it?**  
A: Yes! RenderContext is not frozen, so you can modify fields:
```python
context = RenderContext(role_info=data)
context.template_type = 'hybrid'
context.no_vars = True
```

**Q: When will the old API be removed?**  
A: There are no plans to remove it. Both APIs will coexist to maintain backward compatibility.

**Q: What if I only need to set one or two parameters?**  
A: For very simple cases, the old API might be shorter. But RenderContext is clearer and scales better as complexity grows.

## Summary

- ✅ Import `RenderContext` from `docsible.renderers`
- ✅ Create context object with your parameters
- ✅ Call `render_role_from_context(context, output_path)`
- ✅ Enjoy cleaner, more maintainable code!

The new API is especially beneficial for:
- Complex roles with many diagrams
- Code that needs to be maintained long-term
- Teams where code readability matters
- Projects using type checking (mypy, pyright)

Happy migrating! 
