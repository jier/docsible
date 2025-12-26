"""Shared fixtures for smart defaults tests."""

# Import fixtures from comparison tests for reuse
from tests.comparison.conftest import (
    complex_role,
    complex_role_fixture,
    many_files_role,
    medium_role_fixture,
    minimal_role,
    simple_role,
)

__all__ = [
    "simple_role",
    "complex_role",
    "complex_role_fixture",
    "medium_role_fixture",
    "minimal_role",
    "many_files_role",
]
