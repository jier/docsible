from unittest.mock import MagicMock, patch

from docsible.renderers.processors.metadata_processor import MetadataProcessor


class TestMetadataProcessor:
    """Test MetadataProcessor functionality."""

    def test_init_default_include_metadata(self):
        """Test initialization with default include_metadata=True."""
        processor = MetadataProcessor()
        assert processor.include_metadata is True

    def test_init_include_metadata_false(self):
        """Test initialization with include_metadata=False."""
        processor = MetadataProcessor(include_metadata=False)
        assert processor.include_metadata is False

    def test_add_metadata_success(self, tmp_path):
        """Test adding metadata to content successfully."""
        content = "# My Role\n\nContent here"
        
        mock_metadata = MagicMock()
        mock_metadata.to_comment.return_value = "<!-- metadata -->"
        
        processor = MetadataProcessor()
        
        with patch("docsible.renderers.processors.metadata_processor.generate_metadata") as mock_gen:
            mock_gen.return_value = mock_metadata
            result = processor.add_metadata(content, tmp_path)
        
        assert "<!-- metadata -->" in result
        assert "# My Role" in result
        mock_gen.assert_called_once()

    def test_add_metadata_disabled(self, tmp_path):
        """Test that metadata is not added when disabled."""
        content = "# My Role"
        processor = MetadataProcessor(include_metadata=False)
        
        result = processor.add_metadata(content, tmp_path)
        
        assert result == content

    def test_add_metadata_generation_fails(self, tmp_path):
        """Test that metadata generation failure doesn't break rendering."""
        content = "# My Role"
        processor = MetadataProcessor()
        
        with patch("docsible.renderers.processors.metadata_processor.generate_metadata") as mock_gen:
            mock_gen.side_effect = Exception("Metadata generation failed")
            
            with patch("docsible.renderers.processors.metadata_processor.logger") as mock_logger:
                result = processor.add_metadata(content, tmp_path)
                
                # Should log warning
                mock_logger.warning.assert_called_once()
                assert "Could not generate metadata" in mock_logger.warning.call_args[0][0]
        
        # Should return original content
        assert result == content

    def test_add_metadata_prepends_to_content(self, tmp_path):
        """Test that metadata is prepended with newline."""
        content = "# My Role"
        
        mock_metadata = MagicMock()
        mock_metadata.to_comment.return_value = "<!-- meta -->"
        
        processor = MetadataProcessor()
        
        with patch("docsible.renderers.processors.metadata_processor.generate_metadata") as mock_gen:
            mock_gen.return_value = mock_metadata
            result = processor.add_metadata(content, tmp_path)
        
        # Check that metadata comes first with newline separator
        assert result.startswith("<!-- meta -->\n")
        assert result.endswith("# My Role")
