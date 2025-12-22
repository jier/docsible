"""Handles markdown validation and fixing."""

import logging

from docsible.validators.markdown_fixer import MarkdownFixer
from docsible.validators.markdown_validator import MarkdownValidator
from docsible.validators.models import ValidationSeverity

logger = logging.getLogger(__name__)


class MarkdownProcessor:
    """Processes markdown for validation and fixing."""
    
    def __init__(
        self,
        validate: bool = True,
        auto_fix: bool = False,
        strict_validation: bool = False,
    ):
        """Initialize processor.
        
        Args:
            validate: Run validation
            auto_fix: Automatically fix issues
            strict_validation: Fail on errors
        """
        self.validate = validate
        self.auto_fix = auto_fix
        self.strict_validation = strict_validation
        self.markdown_validator = MarkdownValidator()
        self.markdown_fixer = MarkdownFixer()
    
    def process(self, markdown: str) -> str:
        """Validate and optionally auto-fix markdown formatting.
        
        Args:
            markdown: Raw markdown content
            
        Returns:
            Fixed markdown (if auto_fix=True) or original markdown
            
        Raises:
            ValueError: If strict_validation=True and errors found
        """
        # Auto-fix if enabled (do this first)
        if self.auto_fix:
            original_markdown = markdown
            markdown = self.markdown_fixer.fix_all(markdown)
            if original_markdown != markdown:
                logger.info(
                    f"🔧 Auto-fixed {len(original_markdown) - len(markdown)} formatting issues"
                )
        
        # Validate if enabled
        if self.validate:
            issues = self.markdown_validator.validate(markdown)
            
            if issues:
                self._log_validation_issues(issues)
                
                # Strict mode - fail on errors
                errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
                if self.strict_validation and errors:
                    error_summary = "\n".join(
                        [f"Line {e.line_number}: {e.message}" for e in errors[:10]]
                    )
                    raise ValueError(
                        f"Markdown validation failed with {len(errors)} error(s):\n{error_summary}\n\n"
                        f"Fix template issues or use --no-validate to skip validation."
                    )
                
                # Provide helpful suggestions
                if errors and not self.auto_fix:
                    logger.info(
                        "ℹ️  Run with --auto-fix to automatically correct formatting issues"
                    )
            else:
                logger.info("✓ Markdown validation passed with no issues")
        
        return markdown
    
    def _log_validation_issues(self, issues):
        """Log validation issues by severity."""
        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]
        infos = [i for i in issues if i.severity == ValidationSeverity.INFO]
        
        # Log errors
        if errors:
            logger.error(f"❌ Markdown validation found {len(errors)} error(s):")
            for error in errors[:5]:
                line_info = f" (line {error.line_number})" if error.line_number else ""
                logger.error(f"  {error.message}{line_info}")
            if len(errors) > 5:
                logger.error(f"  ... and {len(errors) - 5} more errors")
        
        # Log warnings
        if warnings:
            logger.warning(f"⚠️  Markdown validation found {len(warnings)} warning(s):")
            for warning in warnings[:3]:
                line_info = f" (line {warning.line_number})" if warning.line_number else ""
                logger.warning(f"  {warning.message}{line_info}")
            if len(warnings) > 3:
                logger.warning(f"  ... and {len(warnings) - 3} more warnings")
        
        # Log infos
        if infos:
            logger.info(f"ℹ️ Markdown validation found {len(infos)} info message(s):")
            for info in infos[:3]:
                line_info = f" (line {info.line_number})" if info.line_number else ""
                logger.info(f" {info.message}{line_info}")
