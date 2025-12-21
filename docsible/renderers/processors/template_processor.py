
import logging
import os

from jinja2 import Environment, FileSystemLoader, Template

from docsible.template_loader import TemplateLoader

logger = logging.getLogger(__name__)


class TemplateProcessor:
    """Handles all template loading operations.

    Consolidates template loading logic from both custom paths and
    the standard TemplateLoader into a unified interface.

    Attributes:
        template_loader: TemplateLoader instance for standard templates
    """

    def __init__(self, template_loader: TemplateLoader | None = None):
        """Initialize processor.

        Args:
            template_loader: Optional custom TemplateLoader instance.
                           Defaults to new TemplateLoader()
        """
        self.template_loader = template_loader or TemplateLoader()

    def get_role_template(
        self,
        template_type: str = "standard",
        custom_path: str | None = None
    ) -> Template:
        """Load role template by type or custom path.

        Args:
            template_type: Template type ('standard', 'hybrid', 'hybrid_modular')
            custom_path: Optional path to custom template file

        Returns:
            Loaded Jinja2 template

        Example:
            >>> processor = TemplateProcessor()
            >>> template = processor.get_role_template('hybrid')
            >>> template = processor.get_role_template(custom_path='/path/to/custom.jinja2')
        """
        if custom_path:
            return self._load_custom_template(custom_path)

        # Log for hybrid templates
        if template_type in ["hybrid", "hybrid_modular"]:
            logger.info("Using hybrid template (manual + auto-generated sections)")

        return self.template_loader.get_role_template(template_type)

    def get_collection_template(self, custom_path: str | None = None) -> Template:
        """Load collection template or custom template.

        Args:
            custom_path: Optional path to custom template file

        Returns:
            Loaded Jinja2 template

        Example:
            >>> processor = TemplateProcessor()
            >>> template = processor.get_collection_template()
        """
        if custom_path:
            return self._load_custom_template(custom_path)

        return self.template_loader.get_collection_template()

    def _load_custom_template(self, template_path: str) -> Template:
        """Load custom template from file path.

        Creates a new Jinja2 environment specific to the custom template's
        directory to allow for relative imports.

        Args:
            template_path: Path to custom template file

        Returns:
            Loaded Jinja2 template

        Raises:
            FileNotFoundError: If template file doesn't exist
            jinja2.TemplateError: If template has syntax errors
        """
        template_dir = os.path.dirname(template_path)
        template_file = os.path.basename(template_path)

        # Create environment for custom template directory
        env = Environment(loader=FileSystemLoader(template_dir))

        logger.info(f"Loading custom template from: {template_path}")
        return env.get_template(template_file)
