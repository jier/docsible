# Installation & Development Guide

This document explains how to install and develop Docsible using different Python package managers.

## Installation

### Using uv (Recommended - Fast!)

```bash
# Install docsible
uv pip install docsible

# Or install from source
uv pip install -e .

# Install with specific Python version
uv pip install --python 3.11 docsible
```

### Using pip

```bash
# Install from PyPI
pip install docsible

# Or install from source
pip install -e .
```

### Using Poetry (Traditional)

```bash
# Install dependencies
poetry install

# Run docsible
poetry run docsible --help
```

## Python Version Management with pyenv

### Setup pyenv

```bash
# Install Python 3.11 (or any version >=3.7)
pyenv install 3.11.0

# Set local Python version
pyenv local 3.11.0

# Verify Python version
python --version
```

### Use with uv + pyenv

```bash
# Set Python version
pyenv local 3.11.0

# Install docsible with uv
uv pip install -e .

# Run docsible
docsible --help
```

### Use with pip + pyenv

```bash
# Set Python version
pyenv local 3.11.0

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install docsible
pip install -e .

# Run docsible
docsible --help
```

## Development Setup

### Using uv (Fastest)

```bash
# Clone repository
git clone https://github.com/docsible/docsible.git
cd docsible

# Install in editable mode with uv
uv pip install -e .

# Run tests
python -m pytest tests/

# Run docsible
docsible --role ./example-role --graph
```

### Using Poetry

```bash
# Clone repository
git clone https://github.com/docsible/docsible.git
cd docsible

# Install dependencies
poetry install

# Run tests
poetry run pytest tests/

# Run docsible
poetry run docsible --role ./example-role --graph
```

### Using pip (Traditional)

```bash
# Clone repository
git clone https://github.com/docsible/docsible.git
cd docsible

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .

# Run tests
pytest tests/

# Run docsible
docsible --role ./example-role --graph
```

## Requirements

- **Python**: 3.7 or higher
- **Dependencies**:
  - click >= 8.1.7
  - PyYAML >= 6.0.1
  - Jinja2 >= 3.1.2

## Tool Comparison

| Tool | Speed | Use Case |
|------|-------|----------|
| **uv** | ⚡ Fastest | Modern development, CI/CD |
| **pip** | 🐢 Slower | Traditional, simple setups |
| **Poetry** | 🐌 Slowest | Existing Poetry projects |

## Supported Python Versions

- Python 3.7
- Python 3.8
- Python 3.9
- Python 3.10
- Python 3.11
- Python 3.12

## Verifying Installation

```bash
# Check version
docsible --version

# Test with help
docsible --help

# Generate example config
docsible-init-config --path .
```

## Troubleshooting

### uv command not found

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### pyenv command not found

```bash
# Install pyenv on macOS/Linux
curl https://pyenv.run | bash

# Or on macOS with Homebrew
brew install pyenv

# Add to shell (add to ~/.bashrc or ~/.zshrc)
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

### Import errors

```bash
# Make sure you're in the right environment
which python
python -c "import docsible; print(docsible.__file__)"

# Reinstall in editable mode
pip install -e .
```

## CI/CD Integration

### Using uv in GitHub Actions

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'

- name: Install uv
  run: pip install uv

- name: Install dependencies
  run: uv pip install -e .

- name: Run docsible
  run: docsible --role ./my-role --graph
```

### Using pip in GitHub Actions

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'

- name: Install dependencies
  run: pip install -e .

- name: Run docsible
  run: docsible --role ./my-role --graph
```

## Building from Source

### Using hatchling (Standard)

```bash
# Install build tool
pip install build

# Build wheel and sdist
python -m build

# Install built wheel
pip install dist/docsible-0.8.0-py3-none-any.whl
```

### Using Poetry

```bash
# Build with poetry
poetry build

# Install built wheel
pip install dist/docsible-0.8.0-py3-none-any.whl
```

## See Also

- [README.md](README.md) - Main documentation
- [CONFIGURATION.md](CONFIGURATION.md) - Project structure configuration
- [pyproject.toml](pyproject.toml) - Package configuration
