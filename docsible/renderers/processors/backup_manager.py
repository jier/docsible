"""Handles file backup operations."""

import logging
import shutil
from datetime import datetime
from pathlib import Path

from docsible import constants

logger = logging.getLogger(__name__)


class BackupManager:
    """Manages file backups before overwriting."""
    
    def create_backup(self, file_path: Path) -> None:
        """Create timestamped backup of existing file.
        
        Args:
            file_path: Path to file to backup
        """
        if not file_path.exists():
            return
            
        timestamp = datetime.now().strftime(constants.BACKUP_TIMESTAMP_FORMAT)
        stem = file_path.stem
        suffix = file_path.suffix
        backup_path = file_path.with_name(f"{stem}_backup_{timestamp}{suffix}")
        
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
