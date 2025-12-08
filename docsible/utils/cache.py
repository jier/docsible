"""Caching utilities for Docsible.

This module provides caching decorators and utilities to improve performance
by avoiding redundant file I/O and expensive operations.
"""

import hashlib
import logging
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

logger = logging.getLogger(__name__)

# Type variables for generic caching
T = TypeVar('T')


def cache_by_file_mtime(func: Callable[[Path], T]) -> Callable[[Path], T]:
    """Cache function results by file modification time.

    This decorator caches the results of functions that load data from files,
    using the file path and modification time as the cache key. If the file
    hasn't been modified since the last call, the cached result is returned.

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
    cache: Dict[Tuple[str, float], T] = {}

    @wraps(func)
    def wrapper(path: Path) -> T:
        """Wrapper function that implements caching logic."""
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
        cache_dict: Dict[Tuple[str, float], T],
        file_path: str,
        current_mtime: float
    ) -> None:
        """Remove old cache entries for the same file path.

        Args:
            cache_dict: Cache dictionary to clean
            file_path: File path to clean entries for
            current_mtime: Current modification time
        """
        keys_to_remove = [
            key for key in cache_dict.keys()
            if key[0] == file_path and key[1] != current_mtime
        ]
        for key in keys_to_remove:
            del cache_dict[key]
            logger.debug(f"Removed stale cache entry: {key}")

    # Add cache inspection methods
    wrapper.cache_info = lambda: {
        "size": len(cache),
        "entries": list(cache.keys())
    }
    wrapper.cache_clear = lambda: cache.clear()

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
    cache: Dict[str, T] = {}

    @wraps(func)
    def wrapper(content: str) -> T:
        """Wrapper function that implements content-based caching."""
        # Generate hash of content
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()

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
    wrapper.cache_info = lambda: {
        "size": len(cache),
        "hashes": list(cache.keys())
    }
    wrapper.cache_clear = lambda: cache.clear()

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


def clear_all_caches() -> None:
    """Clear all LRU caches used by docsible.

    This function clears the cached_resolve_path cache and can be extended
    to clear other caches as needed.

    Example:
        >>> clear_all_caches()  # Clear all caches
    """
    cached_resolve_path.cache_clear()
    logger.info("All caches cleared")


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics about all caches.

    Returns:
        Dictionary with cache statistics

    Example:
        >>> stats = get_cache_stats()
        >>> print(f"Path cache: {stats['path_cache']['hits']} hits")
    """
    return {
        "path_cache": {
            "info": cached_resolve_path.cache_info(),
            "size": cached_resolve_path.cache_info().currsize,
            "maxsize": cached_resolve_path.cache_info().maxsize,
            "hits": cached_resolve_path.cache_info().hits,
            "misses": cached_resolve_path.cache_info().misses,
        }
    }
