from abc import ABC, abstractmethod
from typing import Any

from .models import ValidationIssue, ValidationType


class BaseValidator(ABC):
    type: ValidationType

    @abstractmethod
    def validate(
        self,
        documentation: str,
        role_info: dict[str, Any] | None,
        complexity_report: Any | None,
    ) -> tuple[list[ValidationIssue], dict[str, Any]]:
        ...
