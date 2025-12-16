"""Database operations concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector


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
        return [
            # MySQL/MariaDB
            "mysql_",
            # PostgreSQL
            "postgresql_",
            # MongoDB
            "mongodb_",
            # Redis
            "redis",
            # General DB
            "_db",  # Suffix match: mysql_db, postgresql_db, etc.
            "_user",  # DB user management
            "_query",  # DB queries
        ]

    @property
    def suggested_filename(self) -> str:
        return "database.yml"

    @property
    def priority(self) -> int:
        return 35  # Higher priority due to specific patterns
