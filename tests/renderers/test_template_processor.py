from unittest.mock import MagicMock, patch

from jinja2 import Template

from docsible.renderers.processors.template_processor import TemplateProcessor


class TestTemplateProcessor:
    """Test TemplateProcessor functionality."""

    def test_init_default_template_loader(self):
        """Test initialization with default TemplateLoader."""
        processor = TemplateProcessor()
        assert processor.template_loader is not None

    def test_init_custom_template_loader(self):
        """Test initialization with custom TemplateLoader."""
        mock_loader = MagicMock()
        processor = TemplateProcessor(template_loader=mock_loader)
        assert processor.template_loader is mock_loader

    def test_get_role_template_standard(self):
        """Test loading standard role template."""
        mock_loader = MagicMock()
        mock_template = MagicMock(spec=Template)
        mock_loader.get_role_template.return_value = mock_template

        processor = TemplateProcessor(template_loader=mock_loader)
        result = processor.get_role_template(template_type="standard")

        mock_loader.get_role_template.assert_called_once_with("standard")
        assert result is mock_template

    def test_get_role_template_hybrid(self):
        """Test loading hybrid role template with logging."""
        mock_loader = MagicMock()
        mock_template = MagicMock(spec=Template)
        mock_loader.get_role_template.return_value = mock_template

        processor = TemplateProcessor(template_loader=mock_loader)

        with patch("docsible.renderers.processors.template_processor.logger") as mock_logger:
            result = processor.get_role_template(template_type="hybrid")

            mock_logger.info.assert_called_once()
            assert "hybrid template" in mock_logger.info.call_args[0][0].lower()

        assert result is mock_template

    def test_get_role_template_hybrid_modular(self):
        """Test loading hybrid_modular role template with logging."""
        mock_loader = MagicMock()
        mock_template = MagicMock(spec=Template)
        mock_loader.get_role_template.return_value = mock_template

        processor = TemplateProcessor(template_loader=mock_loader)

        with patch("docsible.renderers.processors.template_processor.logger") as mock_logger:
            result = processor.get_role_template(template_type="hybrid_modular")
            mock_logger.info.assert_called_once()

        assert result is mock_template

    def test_get_role_template_custom_path(self, tmp_path):
        """Test loading role template from custom path."""
        # Create a simple custom template file
        template_file = tmp_path / "custom.jinja2"
        template_file.write_text("# {{ role.name }}")

        processor = TemplateProcessor()
        template = processor.get_role_template(custom_path=str(template_file))

        # Verify it's a valid template
        assert isinstance(template, Template)
        result = template.render(role={"name": "test_role"})
        assert "# test_role" in result

    def test_get_collection_template_standard(self):
        """Test loading standard collection template."""
        mock_loader = MagicMock()
        mock_template = MagicMock(spec=Template)
        mock_loader.get_collection_template.return_value = mock_template

        processor = TemplateProcessor(template_loader=mock_loader)
        result = processor.get_collection_template()

        mock_loader.get_collection_template.assert_called_once()
        assert result is mock_template

    def test_get_collection_template_custom_path(self, tmp_path):
        """Test loading collection template from custom path."""
        # Create a simple custom template file
        template_file = tmp_path / "custom_collection.jinja2"
        template_file.write_text("# {{ collection.namespace }}.{{ collection.name }}")

        processor = TemplateProcessor()
        template = processor.get_collection_template(custom_path=str(template_file))

        # Verify it's a valid template
        assert isinstance(template, Template)
        result = template.render(collection={"namespace": "my", "name": "collection"})
        assert "# my.collection" in result

    def test_load_custom_template_logging(self, tmp_path):
        """Test that custom template loading logs the path."""
        template_file = tmp_path / "test.jinja2"
        template_file.write_text("Test")

        processor = TemplateProcessor()

        with patch("docsible.renderers.processors.template_processor.logger") as mock_logger:
            processor.get_role_template(custom_path=str(template_file))
            mock_logger.info.assert_called_once()
            assert str(template_file) in mock_logger.info.call_args[0][0]

    def test_custom_template_with_subdirectory(self, tmp_path):
        """Test loading custom template from subdirectory."""
        subdir = tmp_path / "templates"
        subdir.mkdir()
        template_file = subdir / "role.jinja2"
        template_file.write_text("# Role: {{ role.name }}")

        processor = TemplateProcessor()
        template = processor.get_role_template(custom_path=str(template_file))

        result = template.render(role={"name": "my_role"})
        assert "# Role: my_role" in result
