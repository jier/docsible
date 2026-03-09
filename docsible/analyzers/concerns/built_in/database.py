"""Database operations concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector
from docsible.analyzers.shared.module_taxonomy import DATABASE_MODULES


class DatabaseOperationsConcern(ConcernDetector):
    """Detects database management and operations tasks."""

    @property
    def concern_name(self) -> str:
        return "database_operations"

    @property
    def display_name(self) -> str:
        return "Database Operations"

    @property
    def description(self) -> str:
        return "Managing databases, schemas, and database operations"

    @property
    def module_patterns(self) -> list:
        # Prefix/suffix patterns for broad matching are kept alongside exact module names.
        # "mysql_", "postgresql_", "mongodb_" are prefix patterns (handled by matches_module).
        # "_db", "_user", "_query" are suffix patterns (handled by matches_module).
        prefix_suffix_patterns = [
            "mysql_",
            "postgresql_",
            "mongodb_",
            "_db",
            "_user",
            "_query",
        ]
        return sorted(DATABASE_MODULES) + prefix_suffix_patterns

    @property
    def suggested_filename(self) -> str:
        return "database.yml"

    @property
    def priority(self) -> int:
        return 35  # Higher priority due to specific patterns
