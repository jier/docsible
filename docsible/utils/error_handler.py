"""Error handling utilities for Docsible.

This module provides decorators and utilities for consistent error handling
across the application.
"""

import logging
from functools import wraps
from pathlib import Path
from typing import Callable, Optional, ParamSpec, TypeVar

from docsible.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def handle_errors(default_return: Optional[T] = None) -> Callable:
    """Decorator to handle and log errors gracefully.

    Catches all exceptions, logs them with full traceback, and returns
    a default value instead of crashing.

    Args:
        default_return: Value to return on error (default: None)

    Returns:
        Decorated function that handles errors gracefully

    Example:
        @handle_errors(default_return={})
        def load_config(path: Path) -> Dict:
            # ... might raise exception
            return config

        # If error occurs, returns {} and logs the error
        config = load_config(path)
    """

    def decorator(func: Callable[P, T]) -> Callable[P, Optional[T]]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Error in {func.__name__}: {e}")
                return default_return

        return wrapper

    return decorator


def validate_path(
    path: Path,
    must_exist: bool = True,
    must_be_dir: bool = False,
    must_be_file: bool = False,
    description: str = "Path",
) -> None:
    """Validate a filesystem path.

    Args:
        path: Path to validate
        must_exist: Whether path must exist (default: True)
        must_be_dir: Whether path must be a directory (default: False)
        must_be_file: Whether path must be a file (default: False)
        description: Human-readable description for error messages

    Raises:
        ConfigurationError: If validation fails

    Example:
        validate_path(role_path, must_exist=True, must_be_dir=True, description="Role directory")
    """
    if must_exist and not path.exists():
        raise ConfigurationError(f"{description} does not exist: {path}")

    if must_be_dir and not path.is_dir():
        raise ConfigurationError(f"{description} is not a directory: {path}")

    if must_be_file and not path.is_file():
        raise ConfigurationError(f"{description} is not a file: {path}")


def validate_role_structure(role_path: Path, strict: bool = False) -> None:
    """Validate that a path contains a valid Ansible role structure.

    Args:
        role_path: Path to role directory
        strict: If True, require all standard directories (tasks, defaults, meta)
                If False, only check that path exists and is a directory

    Raises:
        ConfigurationError: If role structure is invalid

    Example:
        validate_role_structure(Path("/path/to/role"), strict=True)
    """
    validate_path(
        role_path, must_exist=True, must_be_dir=True, description="Role directory"
    )

    if strict:
        # Check for at least one standard role directory
        standard_dirs = [
            "tasks",
            "defaults",
            "vars",
            "meta",
            "handlers",
            "templates",
            "files",
        ]
        found_dirs = [d for d in standard_dirs if (role_path / d).exists()]

        if not found_dirs:
            raise ConfigurationError(
                f"No standard Ansible role directories found in {role_path}. "
                f"Expected at least one of: {', '.join(standard_dirs)}"
            )


def safe_read_file(file_path: Path, encoding: str = "utf-8") -> Optional[str]:
    """Safely read a file, returning None on error.

    Args:
        file_path: Path to file to read
        encoding: File encoding (default: 'utf-8')

    Returns:
        File contents as string, or None if error occurs

    Example:
        content = safe_read_file(Path("config.yml"))
        if content:
            # Process content
            pass
    """
    try:
        return file_path.read_text(encoding=encoding)
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
        logger.warning(f"Failed to read file {file_path}: {e}")
        return None


def safe_write_file(file_path: Path, content: str, encoding: str = "utf-8") -> bool:
    """Safely write content to a file, returning success status.

    Args:
        file_path: Path to file to write
        content: Content to write
        encoding: File encoding (default: 'utf-8')

    Returns:
        True if write succeeded, False otherwise

    Example:
        if safe_write_file(Path("README.md"), readme_content):
            print("✓ File written successfully")
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding=encoding)
        return True
    except (PermissionError, OSError) as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        return False


def log_and_exit(message: str, exit_code: int = 1) -> None:
    """Log an error message and exit the program.

    Args:
        message: Error message to log and display
        exit_code: Exit code for the program (default: 1)

    Example:
        log_and_exit("Configuration file not found", exit_code=2)
    """
    import sys

    logger.error(message)
    sys.exit(exit_code)
