"""Renderers for generating documentation from templates."""

# Export models for convenience (users can import from here)
from docsible.renderers.models import (
    DependencyData,
    DiagramData,
    RenderConfig,
    RenderFlags,
)

# Export processors (advanced users might need them)
from docsible.renderers.processors import (
    BackupManager,
    ContentMerger,
    MarkdownProcessor,
)
from docsible.renderers.readme_renderer import ReadmeRenderer
from docsible.renderers.tag_manager import (
    manage_docsible_file_keys,
    manage_docsible_tags,
    replace_between_tags,
)

__all__ = [
    # Main renderer
    "ReadmeRenderer",

    # Tag management
    "manage_docsible_file_keys",
    "manage_docsible_tags",
    "replace_between_tags",
    
    # Models
    "RenderConfig",
    "RenderFlags",
    "DiagramData",
    "DependencyData",
    
    # Processors
    "BackupManager",
    "ContentMerger",
    "MarkdownProcessor",
]
