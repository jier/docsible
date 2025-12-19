from pathlib import Path

import yaml

from docsible.renderers.tag_manager import manage_docsible_file_keys


def test_dt_update():
    """Test that manage_docsible_file_keys initializes file with default keys."""
    test_file = Path(".docsible_test_dt_update")

    try:
        # Call manage_docsible_file_keys to create/update the file
        result = manage_docsible_file_keys(test_file)

        # Verify file was created
        assert test_file.exists()

        # Verify result contains expected keys
        assert "dt_update" in result
        assert "description" in result
        assert "version" in result

        # Read file and verify structure
        with open(test_file) as f:
            data = yaml.safe_load(f)

        # dt_update should exist (even if empty initially)
        assert "dt_update" in data

    finally:
        # Cleanup: remove the test file if it exists
        if test_file.exists():
            test_file.unlink()
