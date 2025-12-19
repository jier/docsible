"""Template loading and management for Docsible."""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

from docsible.utils.mermaid.pagination import get_diagram_complexity_warning
from docsible.utils.template_filters import TEMPLATE_FILTERS

logger = logging.getLogger(__name__)


class TemplateLoader:
    """Load and cache Jinja2 templates for documentation generation.

    Provides access to role, collection, and partial templates with
    automatic caching and proper error handling.

    Attributes:
        template_dir: Path to templates directory
        env: Jinja2 environment instance
    """

    def __init__(self, template_dir: Path | None = None):
        """Initialize TemplateLoader.

        Args:
            template_dir: Optional custom template directory.
                         Defaults to docsible/templates/

        Example:
            >>> loader = TemplateLoader()
            >>> template = loader.get_template('role/hybrid.jinja2')
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = template_dir
        # Define search paths in priority order
        # When a template does {% import 'macros/utils.j2' %},
        # Jinja2 will search these paths in order:
        search_paths = [
            str(self.template_dir / "role"),  # 1. role/macros/utils.j2
            str(self.template_dir / "collection"),  # 2. collection/macros/utils.j2
            str(self.template_dir),  # 3. macros/utils.j2 (fallback)
        ]
        self.env = Environment(
            loader=FileSystemLoader(search_paths),
            trim_blocks=False,
            lstrip_blocks=False,
            keep_trailing_newline=True,
        )

        # Register custom filters for safe table rendering
        self.env.filters.update(TEMPLATE_FILTERS)

        # Register global helper functions
        self.env.globals["get_diagram_complexity_warning"] = (
            get_diagram_complexity_warning
        )

        logger.debug(f"Initialized TemplateLoader with search paths: {search_paths}")

    def get_template(self, name: str) -> Template:
        """Load template by name.

        Args:
            name: Template name relative to templates directory
                  (e.g., 'role/hybrid.jinja2', 'collection/main.jinja2')

        Returns:
            Compiled Jinja2 template

        Raises:
            jinja2.TemplateNotFound: If template doesn't exist

        Example:
            >>> loader = TemplateLoader()
            >>> template = loader.get_template('role/standard.jinja2')
            >>> content = template.render(role=role_data)
        """
        logger.debug(f"Loading template: {name}")
        return self.env.get_template(name)

    def get_role_template(self, template_type: str = "standard") -> Template:
        """Get role documentation template by type.

        Args:
            template_type: Template type ('standard' or 'hybrid')

        Returns:
            Compiled Jinja2 template

        Example:
            >>> loader = TemplateLoader()
            >>> template = loader.get_role_template('hybrid')
        """
        template_map = {
            "standard": "role/standard.jinja2",
            "standard_modular": "role/standard_modular.jinja2",
            "hybrid": "role/hybrid_modular.jinja2",
            "hybrid_modular": "role/hybrid.jinja2",
        }

        template_name = template_map.get(template_type)
        if not template_name:
            logger.warning(
                f"Unknown template type '{template_type}', falling back to 'standard'"
            )
            template_name = template_map["standard"]

        return self.get_template(template_name)

    def get_collection_template(self) -> Template:
        """Get collection documentation template.

        Returns:
            Compiled Jinja2 template for collection documentation

        Example:
            >>> loader = TemplateLoader()
            >>> template = loader.get_collection_template()
        """
        return self.get_template("collection/main.jinja2")

    def list_templates(self) -> list[str]:
        """List all available templates.

        Returns:
            List of template names relative to templates directory

        Example:
            >>> loader = TemplateLoader()
            >>> templates = loader.list_templates()
            >>> print(templates)
            ['role/standard.jinja2', 'role/hybrid.jinja2', 'collection/main.jinja2']
        """
        templates = []
        for template_file in self.template_dir.rglob("*.jinja2"):
            relative_path = template_file.relative_to(self.template_dir)
            templates.append(str(relative_path))

        logger.debug(f"Found {len(templates)} templates")
        return sorted(templates)
