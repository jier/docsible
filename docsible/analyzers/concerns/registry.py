"""Registry for concern detectors."""

import logging
from typing import Any, Dict, List, Optional, Type

from .base import ConcernDetector, ConcernMatch

logger = logging.getLogger(__name__)


class ConcernRegistry:
    """
    Central registry for all concern detectors.

    Supports:
    - Auto-registration of built-in concerns
    - Manual registration of custom concerns
    - Detection across all registered concerns
    - Priority-based conflict resolution

    Example:
        >>> from docsible.analyzers.concerns.registry import ConcernRegistry
        >>> matches = ConcernRegistry.detect_all(tasks)
        >>> primary = ConcernRegistry.detect_primary_concern(tasks)
    """

    _detectors: List[ConcernDetector] = []
    _initialized: bool = False

    @classmethod
    def register(cls, detector: ConcernDetector) -> None:
        """
        Register a concern detector.

        Args:
            detector: Instance of ConcernDetector

        Example:
            >>> detector = PackageInstallationConcern()
            >>> ConcernRegistry.register(detector)
        """
        if detector not in cls._detectors:
            cls._detectors.append(detector)
            logger.debug(f"Registered concern detector: {detector.display_name}")

    @classmethod
    def register_class(cls, detector_class: Type[ConcernDetector]) -> None:
        """
        Register a concern detector class (instantiates it).

        Args:
            detector_class: ConcernDetector subclass

        Example:
            >>> ConcernRegistry.register_class(PackageInstallationConcern)
        """
        detector = detector_class()
        cls.register(detector)

    @classmethod
    def auto_register_builtin(cls) -> None:
        """
        Auto-register all built-in concern detectors.

        Imports and registers all detectors from concerns/built_in/.
        """
        if cls._initialized:
            return

        try:
            from docsible.analyzers.concerns.built_in import (
                ArtifactManagementConcern,
                ConfigurationConcern,
                DatabaseOperationsConcern,
                FilesystemManagementConcern,
                IdentityPermissionConcern,
                NetworkConfigurationConcern,
                PackageInstallationConcern,
                ServiceManagementConcern,
                VerificationConcern,
                WindowsPowerShellConcern,
            )

            # Register all built-in concerns
            for detector_class in [
                PackageInstallationConcern,
                ConfigurationConcern,
                ServiceManagementConcern,
                IdentityPermissionConcern,
                FilesystemManagementConcern,
                NetworkConfigurationConcern,
                WindowsPowerShellConcern,
                ArtifactManagementConcern,
                DatabaseOperationsConcern,
                VerificationConcern,
            ]:
                cls.register_class(detector_class)

            cls._initialized = True
            logger.info(f"Registered {len(cls._detectors)} built-in concern detectors")

        except ImportError as e:
            logger.warning(f"Could not auto-register built-in concerns: {e}")

    @classmethod
    def detect_all(cls, tasks: List[Dict[str, Any]]) -> List[ConcernMatch]:
        """
        Run all registered detectors on tasks.

        Args:
            tasks: List of task dictionaries

        Returns:
            List of ConcernMatch objects, sorted by confidence (descending)

        Example:
            >>> tasks = [{"module": "apt"}, {"module": "template"}]
            >>> matches = ConcernRegistry.detect_all(tasks)
            >>> matches[0].concern_name
            'package_installation'
        """
        cls.auto_register_builtin()

        if not tasks:
            return []

        matches = []
        for detector in cls._detectors:
            match = detector.detect(tasks)
            if match.task_count > 0:  # Only include if something matched
                matches.append(match)

        # Sort by confidence (descending)
        matches.sort(key=lambda m: m.confidence, reverse=True)

        return matches

    @classmethod
    def detect_primary_concern(
        cls, tasks: List[Dict[str, Any]], min_confidence: float = 0.6
    ) -> Optional[ConcernMatch]:
        """
        Detect the primary (dominant) concern in tasks.

        Args:
            tasks: List of task dictionaries
            min_confidence: Minimum confidence threshold (default: 0.6)

        Returns:
            Primary ConcernMatch if found, None otherwise

        Example:
            >>> primary = ConcernRegistry.detect_primary_concern(tasks)
            >>> if primary:
            ...     print(f"Primary concern: {primary.display_name}")
        """
        matches = cls.detect_all(tasks)

        if not matches:
            return None

        # Primary concern is the highest confidence match above threshold
        primary = matches[0]
        if primary.confidence >= min_confidence:
            return primary

        return None  # No dominant concern

    @classmethod
    def get_detector(cls, concern_name: str) -> Optional[ConcernDetector]:
        """
        Get a specific detector by concern name.

        Args:
            concern_name: Concern identifier (e.g., 'package_installation')

        Returns:
            ConcernDetector instance or None
        """
        cls.auto_register_builtin()

        for detector in cls._detectors:
            if detector.concern_name == concern_name:
                return detector

        return None

    @classmethod
    def list_concerns(cls) -> List[str]:
        """
        List all registered concern names.

        Returns:
            List of concern name strings
        """
        cls.auto_register_builtin()
        return [d.concern_name for d in cls._detectors]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered detectors (mainly for testing)."""
        cls._detectors = []
        cls._initialized = False
