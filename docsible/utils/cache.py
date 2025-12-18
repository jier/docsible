"""Caching utilities for Docsible.

This module provides caching decorators and utilities to improve performance
by avoiding redundant file I/O and expensive operations.
"""

import hashlib
import logging
from collections.abc import Callable
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# Type variables for generic caching
T = TypeVar("T")


# ============================================================================
# Cache Configuration
# ============================================================================

class CacheConfig:
    """Global cache configuration.

    Controls cache sizes, TTL, and enable/disable state.
    Can be configured via environment variables or programmatically.
    """

    # Maximum cache sizes
    YAML_CACHE_SIZE = 1000      # ~100MB for 1000 average YAML files
    ANALYSIS_CACHE_SIZE = 200   # ~50MB for 200 role analyses
    PATH_CACHE_SIZE = 512       # ~1MB for path operations

    # Enable/disable caching globally
    CACHING_ENABLED = True      # Can be disabled for debugging

    @classmethod
    def from_env(cls) -> None:
        """Load configuration from environment variables."""
        import os

        # Check if caching is disabled
        if os.getenv("DOCSIBLE_DISABLE_CACHE") == "1":
            cls.CACHING_ENABLED = False
            logger.info("Caching disabled via DOCSIBLE_DISABLE_CACHE")

        # Custom cache sizes
        if yaml_size := os.getenv("DOCSIBLE_YAML_CACHE_SIZE"):
            cls.YAML_CACHE_SIZE = int(yaml_size)

        if analysis_size := os.getenv("DOCSIBLE_ANALYSIS_CACHE_SIZE"):
            cls.ANALYSIS_CACHE_SIZE = int(analysis_size)


def configure_caches(*,
                     yaml_size: int | None = None,
                     analysis_size: int | None = None,
                     enabled: bool | None = None) -> None:
    """Configure all caches globally.

    Args:
        yaml_size: Maximum YAML cache entries
        analysis_size: Maximum analysis cache entries
        enabled: Enable/disable caching

    Example:
        >>> configure_caches(enabled=False)  # Disable for debugging
        >>> configure_caches(yaml_size=500)  # Reduce memory usage
    """
    if yaml_size is not None:
        CacheConfig.YAML_CACHE_SIZE = yaml_size
    if analysis_size is not None:
        CacheConfig.ANALYSIS_CACHE_SIZE = analysis_size
    if enabled is not None:
        CacheConfig.CACHING_ENABLED = enabled
        logger.info(f"Caching {'enabled' if enabled else 'disabled'}")


# Initialize from environment on import
CacheConfig.from_env()


def cache_by_file_mtime(func: Callable[[Path], T]) -> Callable[[Path], T]:
    """Cache function results by file modification time.

    This decorator caches the results of functions that load data from files,
    using the file path and modification time as the cache key. If the file
    hasn't been modified since the last call, the cached result is returned.

    Respects CacheConfig.CACHING_ENABLED flag - can be disabled globally.

    Args:
        func: Function that takes a Path and returns data

    Returns:
        Cached version of the function

    Example:
        @cache_by_file_mtime
        def load_yaml_file(path: Path) -> dict:
            with open(path) as f:
                return yaml.safe_load(f)

        # First call reads from disk
        data1 = load_yaml_file(Path("config.yml"))

        # Second call returns cached result (if file unchanged)
        data2 = load_yaml_file(Path("config.yml"))
    """
    cache: dict[tuple[str, float], T] = {}

    @wraps(func)
    def wrapper(path: Path) -> T:
        """Wrapper function that implements caching logic."""
        # If caching is disabled, bypass cache
        if not CacheConfig.CACHING_ENABLED:
            return func(path)

        try:
            # Get file modification time
            mtime = path.stat().st_mtime
            cache_key = (str(path), mtime)

            # Return cached result if available
            if cache_key in cache:
                logger.debug(f"Cache hit for {path}")
                return cache[cache_key]

            # Call function and cache result
            logger.debug(f"Cache miss for {path}, loading from disk")
            result = func(path)
            cache[cache_key] = result

            # Clean old cache entries for this path
            _clean_old_entries(cache, str(path), mtime)

            return result

        except FileNotFoundError:
            logger.warning(f"File not found: {path}")
            return func(path)  # Let the original function handle the error
        except Exception as e:
            logger.error(f"Error accessing file {path}: {e}")
            return func(path)  # Let the original function handle the error

    def _clean_old_entries(
        cache_dict: dict[tuple[str, float], T], file_path: str, current_mtime: float
    ) -> None:
        """Remove old cache entries for the same file path.

        Args:
            cache_dict: Cache dictionary to clean
            file_path: File path to clean entries for
            current_mtime: Current modification time
        """
        keys_to_remove = [
            key
            for key in cache_dict.keys()
            if key[0] == file_path and key[1] != current_mtime
        ]
        for key in keys_to_remove:
            del cache_dict[key]
            logger.debug(f"Removed stale cache entry: {key}")

    # Add cache inspection methods
    wrapper.cache_info = lambda: {"size": len(cache), "entries": list(cache.keys())}  # type: ignore[attr-defined]
    wrapper.cache_clear = lambda: cache.clear()  # type: ignore[attr-defined]

    # Register this cache for global management
    _register_yaml_cache(wrapper)

    return wrapper


def cache_by_dir_mtime(func: Callable[..., T]) -> Callable[..., T]:
    """Cache function results by directory modification times.

    This decorator caches the results of functions that analyze entire directories,
    using the directory path and a hash of all file modification times as the cache key.
    If any file in the directory has been modified, the cache is invalidated.

    Respects CacheConfig.CACHING_ENABLED flag - can be disabled globally.

    Args:
        func: Function that takes a directory Path as first argument and returns analysis results

    Returns:
        Cached version of the function

    Example:
        @cache_by_dir_mtime
        def analyze_role_complexity_cached(role_path: Path, include_patterns: bool = False) -> ComplexityReport:
            # ... expensive analysis ...
            return report

        # First call analyzes from disk
        report1 = analyze_role_complexity_cached(Path("./roles/webserver"))

        # Second call returns cached result (if no files changed)
        report2 = analyze_role_complexity_cached(Path("./roles/webserver"))
    """
    cache: dict[tuple[str, str, str], T] = {}  # (path, args_hash, files_hash) -> result

    @wraps(func)
    def wrapper(path: Path, *args: Any, **kwargs: Any) -> T:
        """Wrapper function that implements caching logic."""
        # If caching is disabled, bypass cache
        if not CacheConfig.CACHING_ENABLED:
            return func(path, *args, **kwargs)

        try:
            import hashlib

            # Create hash of function arguments (excluding path)
            args_str = f"{args}:{sorted(kwargs.items())}"
            args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]

            # Compute hash of all file mtimes in directory
            files_hash = _compute_dir_mtime_hash(path)
            cache_key = (str(path), args_hash, files_hash)

            # Return cached result if available
            if cache_key in cache:
                logger.debug(f"Cache hit for directory {path}")
                return cache[cache_key]

            # Call function and cache result
            logger.debug(f"Cache miss for directory {path}, analyzing...")
            result = func(path, *args, **kwargs)
            cache[cache_key] = result

            # Clean old cache entries for this path
            _clean_old_dir_entries(cache, str(path))

            return result

        except FileNotFoundError:
            logger.warning(f"Directory not found: {path}")
            return func(path, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error accessing directory {path}: {e}")
            return func(path, *args, **kwargs)

    def _compute_dir_mtime_hash(dir_path: Path) -> str:
        """Compute hash of all file modification times in directory.

        Args:
            dir_path: Directory to hash

        Returns:
            MD5 hash of all file mtimes (first 16 chars)
        """
        import hashlib
        import os

        if not dir_path.exists() or not dir_path.is_dir():
            return "nonexistent"

        # Collect all file paths and mtimes
        file_mtimes: list[tuple[str, float]] = []

        # Walk through directory
        for root, _, files in os.walk(dir_path):
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                try:
                    mtime = file_path.stat().st_mtime
                    # Use relative path for consistency
                    rel_path = file_path.relative_to(dir_path)
                    file_mtimes.append((str(rel_path), mtime))
                except (OSError, ValueError):
                    continue

        # Sort for consistency
        file_mtimes.sort()

        # Create hash
        hash_str = "|".join(f"{path}:{mtime}" for path, mtime in file_mtimes)
        return hashlib.md5(hash_str.encode()).hexdigest()[:16]

    def _clean_old_dir_entries(
        cache_dict: dict[tuple[str, str, str], T], dir_path: str
    ) -> None:
        """Remove old cache entries for the same directory path.

        Keeps only the most recent entry for each (path, args) combination.

        Args:
            cache_dict: Cache dictionary to clean
            dir_path: Directory path to clean entries for
        """
        # Group by (path, args_hash)
        path_args_to_files_hash: dict[tuple[str, str], list[str]] = {}
        for key in cache_dict.keys():
            if key[0] == dir_path:
                path_args = (key[0], key[1])
                files_hash = key[2]
                if path_args not in path_args_to_files_hash:
                    path_args_to_files_hash[path_args] = []
                path_args_to_files_hash[path_args].append(files_hash)

        # Remove all but the most recent files_hash for each (path, args)
        keys_to_remove = []
        for (path, args_hash), files_hashes in path_args_to_files_hash.items():
            if len(files_hashes) > 1:
                # Keep the first one we just added, remove others
                for files_hash in files_hashes[:-1]:
                    keys_to_remove.append((path, args_hash, files_hash))

        for key in keys_to_remove:
            if key in cache_dict:
                del cache_dict[key]
                logger.debug(f"Removed stale cache entry: {key}")

    # Add cache inspection methods
    wrapper.cache_info = lambda: {"size": len(cache), "entries": list(cache.keys())}  # type: ignore[attr-defined]
    wrapper.cache_clear = lambda: cache.clear()  # type: ignore[attr-defined]

    # Register this cache for global management
    _register_yaml_cache(wrapper)

    return wrapper


def cache_by_content_hash(func: Callable[[str], T]) -> Callable[[str], T]:
    """Cache function results by content hash.

    This decorator caches results based on the hash of the input content,
    useful for functions that process strings or data.

    Args:
        func: Function that takes string content and returns processed data

    Returns:
        Cached version of the function

    Example:
        @cache_by_content_hash
        def parse_yaml_string(content: str) -> dict:
            return yaml.safe_load(content)

        # First call processes content
        data1 = parse_yaml_string(yaml_content)

        # Second call with same content returns cached result
        data2 = parse_yaml_string(yaml_content)
    """
    cache: dict[str, T] = {}

    @wraps(func)
    def wrapper(content: str) -> T:
        """Wrapper function that implements content-based caching."""
        # Generate hash of content
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()

        # Return cached result if available
        if content_hash in cache:
            logger.debug(f"Cache hit for content hash {content_hash[:8]}...")
            return cache[content_hash]

        # Call function and cache result
        logger.debug(f"Cache miss for content hash {content_hash[:8]}...")
        result = func(content)
        cache[content_hash] = result

        return result

    # Add cache inspection methods
    wrapper.cache_info = lambda: {"size": len(cache), "hashes": list(cache.keys())}  # type: ignore[attr-defined]
    wrapper.cache_clear = lambda: cache.clear()  # type: ignore[attr-defined]

    return wrapper


@lru_cache(maxsize=128)
def cached_resolve_path(path_str: str) -> Path:
    """Cache resolved absolute paths.

    Args:
        path_str: Path string to resolve

    Returns:
        Resolved absolute Path object

    Example:
        >>> path1 = cached_resolve_path("./config.yml")
        >>> path2 = cached_resolve_path("./config.yml")  # Returns cached result
        >>> path1 is path2
        True
    """
    return Path(path_str).resolve()


# Track all caches for management
_YAML_CACHES: list[Any] = []  # Store references to YAML cache wrappers


def _register_yaml_cache(wrapper: Any) -> None:
    """Register a YAML cache wrapper for management."""
    _YAML_CACHES.append(wrapper)


def clear_all_caches() -> None:
    """Clear all caches used by docsible.

    Clears:
    - Path resolution cache
    - YAML file caches (registered via @cache_by_file_mtime)

    Example:
        >>> clear_all_caches()  # Clear all caches
        >>> # Useful for testing or troubleshooting
    """
    # Clear LRU caches
    cached_resolve_path.cache_clear()

    # Clear YAML caches
    for cache_wrapper in _YAML_CACHES:
        if hasattr(cache_wrapper, 'cache_clear'):
            cache_wrapper.cache_clear()

    logger.info("All caches cleared")


def get_cache_stats() -> dict[str, Any]:
    """Get statistics about all caches.

    Returns:
        Dictionary with cache statistics including:
        - path_cache: Path resolution cache stats
        - yaml_caches: List of YAML cache stats
        - total_entries: Total cached entries across all caches

    Example:
        >>> stats = get_cache_stats()
        >>> print(f"Path cache: {stats['path_cache']['hits']} hits")
        >>> print(f"Total YAML caches: {len(stats['yaml_caches'])}")
    """
    path_info = cached_resolve_path.cache_info()

    yaml_cache_stats = []
    total_yaml_entries = 0

    for cache_wrapper in _YAML_CACHES:
        if hasattr(cache_wrapper, 'cache_info'):
            info = cache_wrapper.cache_info()
            yaml_cache_stats.append(info)
            total_yaml_entries += info.get('size', 0)

    return {
        "caching_enabled": CacheConfig.CACHING_ENABLED,
        "path_cache": {
            "info": path_info,
            "size": path_info.currsize,
            "maxsize": path_info.maxsize,
            "hits": path_info.hits,
            "misses": path_info.misses,
            "hit_rate": path_info.hits / (path_info.hits + path_info.misses)
            if (path_info.hits + path_info.misses) > 0
            else 0.0,
        },
        "yaml_caches": yaml_cache_stats,
        "total_yaml_entries": total_yaml_entries,
        "total_entries": path_info.currsize + total_yaml_entries,
    }
