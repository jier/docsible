# Docsible Troubleshooting Guide

Common issues and how to fix them.

## Role Not Found

**Error:** `Role path is required` or `No such file or directory`

**Solutions:**
```bash
# Use absolute path
docsible role --role /absolute/path/to/role

# Or relative from current directory
cd /path/to/roles
docsible role --role ./my-role

# Verify the path exists
ls -la ./my-role
```

## No README Generated

**Problem:** Command runs but no README.md appears

**Check:**
```bash
# Ensure role has tasks/
ls -la ./my-role/tasks/

# Run in dry-run mode to preview
docsible role --role . --dry-run

# Check current directory
pwd
ls -la
```

## Output Looks Empty

**Problem:** README is generated but missing sections

**Solutions:**
```bash
# Check what's being detected
docsible role --role . --dry-run

# Enable all content
docsible role --role . --no-minimal

# Check for variables
ls -la defaults/ vars/
```

## Diagrams Not Generating

**Problem:** No Mermaid diagrams in README

**Solution:**
```bash
# Explicitly enable graphs
docsible role --role . --graph
```

## Too Many Warnings

**Problem:** Output has lots of recommendations

**Solutions:**
```bash
# Show only critical issues
docsible role --role . --recommendations-only

# Hide INFO-level suggestions (they're hidden by default)
# Use --show-info to see them explicitly
docsible role --role . --show-info

# Use neutral mode to skip positive framing
docsible role --role . --neutral
```

## Performance Issues

**Problem:** Documentation takes too long

**Solutions:**
```bash
# Use minimal mode for faster output
docsible role --role . --minimal

# Skip diagrams
docsible role --role . --no-diagrams
```

## Getting More Help

```bash
docsible role --help-full       # All available options
docsible guide getting-started  # Start from the beginning
docsible guide smart-defaults   # Understand auto-detection
```

---

*For more help: https://docs.docsible.com*
