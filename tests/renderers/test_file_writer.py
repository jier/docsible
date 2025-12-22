"""Tests for FileWriter."""

from unittest.mock import patch

from docsible.renderers.processors.file_writer import FileWriter


class TestFileWriter:
    """Test FileWriter functionality."""

    def test_write_creates_file(self, tmp_path):
        """Test that write creates file with content."""
        output_path = tmp_path / "README.md"
        content = "# My Role\n\nTest content"
        
        writer = FileWriter()
        writer.write(output_path, content)
        
        assert output_path.exists()
        assert output_path.read_text() == content

    def test_write_creates_parent_directories(self, tmp_path):
        """Test that write creates parent directories if missing."""
        output_path = tmp_path / "subdir" / "nested" / "README.md"
        content = "# Test"
        
        writer = FileWriter()
        writer.write(output_path, content)
        
        assert output_path.exists()
        assert output_path.read_text() == content

    def test_write_overwrites_existing_file(self, tmp_path):
        """Test that write overwrites existing file."""
        output_path = tmp_path / "README.md"
        output_path.write_text("Old content")
        
        new_content = "New content"
        writer = FileWriter()
        writer.write(output_path, new_content)
        
        assert output_path.read_text() == new_content

    def test_write_uses_utf8_encoding(self, tmp_path):
        """Test that write uses UTF-8 encoding for unicode content."""
        output_path = tmp_path / "README.md"
        content = "# My Role\n\n✓ Unicode: 你好 🎉"
        
        writer = FileWriter()
        writer.write(output_path, content)
        
        # Read back and verify UTF-8 was used
        assert output_path.read_text(encoding="utf-8") == content

    def test_write_logs_success(self, tmp_path):
        """Test that write logs success message."""
        output_path = tmp_path / "README.md"
        content = "# Test"
        
        writer = FileWriter()
        
        with patch("docsible.renderers.processors.file_writer.logger") as mock_logger:
            writer.write(output_path, content)
            
            mock_logger.info.assert_called_once()
            assert str(output_path) in mock_logger.info.call_args[0][0]
            assert "✓" in mock_logger.info.call_args[0][0]

    def test_write_multiline_content(self, tmp_path):
        """Test writing multiline content."""
        output_path = tmp_path / "README.md"
        content = "Line 1\nLine 2\nLine 3\n"
        
        writer = FileWriter()
        writer.write(output_path, content)
        
        assert output_path.read_text() == content

    def test_write_empty_content(self, tmp_path):
        """Test writing empty content."""
        output_path = tmp_path / "README.md"
        content = ""
        
        writer = FileWriter()
        writer.write(output_path, content)
        
        assert output_path.exists()
        assert output_path.read_text() == ""

    def test_write_large_content(self, tmp_path):
        """Test writing large content."""
        output_path = tmp_path / "README.md"
        content = "# Header\n" + ("Line\n" * 10000)
        
        writer = FileWriter()
        writer.write(output_path, content)
        
        assert output_path.exists()
        assert len(output_path.read_text().split("\n")) > 10000
