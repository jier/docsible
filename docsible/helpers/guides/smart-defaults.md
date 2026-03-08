# Smart Defaults in Docsible

Docsible automatically adjusts documentation based on your role's complexity.

## How It Works

When you run `docsible role --role .`, Docsible:

1. **Analyzes your role** — counts tasks, handlers, dependencies
2. **Classifies complexity** — SIMPLE (1-10 tasks), MEDIUM (11-25), COMPLEX (25+)
3. **Applies smart defaults** — adjusts settings for best output

## Complexity Categories

| Category | Tasks | Auto Behavior |
|----------|-------|---------------|
| SIMPLE | 1-10 | Minimal docs, no graphs |
| MEDIUM | 11-25 | Standard docs |
| COMPLEX | 25+ | Full docs + graphs + dependencies |

## Viewing Analysis

```bash
# See complexity without generating docs
docsible role --role . --analyze-only

# Include complexity report in README
docsible role --role . --complexity-report
```

## Override Smart Defaults

```bash
# Force graph generation (even for simple roles)
docsible role --role . --graph

# Force minimal mode (even for complex roles)
docsible role --role . --minimal

# Show dependency matrix
docsible role --role . --show-dependencies
```

## Disable Smart Defaults

Set environment variable:
```bash
DOCSIBLE_ENABLE_SMART_DEFAULTS=false docsible role --role .
```

## What Gets Auto-Detected

- **Graph generation**: Enabled for COMPLEX roles automatically
- **Minimal mode**: Enabled for SIMPLE roles (fewer sections)
- **Dependencies**: Shown for roles with many dependencies

---

*For more help: docsible guide getting-started*
