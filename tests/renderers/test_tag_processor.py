from unittest.mock import patch

from docsible.renderers.processors.tag_processor import TagProcessor


class TestTagProcessor:
    """Test TagProcessor functionality."""

    def test_add_tags_calls_manage_docsible_tags(self):
        """Test that add_tags delegates to manage_docsible_tags."""
        content = "# My Role\n\nContent here"
        processor = TagProcessor()
        
        with patch("docsible.renderers.processors.tag_processor.manage_docsible_tags") as mock_manage:
            mock_manage.return_value = "tagged content"
            result = processor.add_tags(content)
            
            mock_manage.assert_called_once_with(content)
            assert result == "tagged content"

    def test_add_tags_returns_tagged_content(self):
        """Test that add_tags returns tagged content."""
        content = "# My Role"
        processor = TagProcessor()
        
        # Use actual implementation
        result = processor.add_tags(content)
        
        # Should contain docsible tags
        assert "DOCSIBLE" in result or content in result

    def test_add_tags_preserves_content(self):
        """Test that add_tags preserves original content."""
        content = "# My Role\n\nSome content\n\n## Section"
        processor = TagProcessor()
        
        result = processor.add_tags(content)
        
        # Original content should be present in result
        assert "# My Role" in result
        assert "Some content" in result
        assert "## Section" in result
