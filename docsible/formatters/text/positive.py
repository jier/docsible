import time
from pathlib import Path

from docsible.analyzers.complexity_analyzer.models import ComplexityCategory, ComplexityReport
from docsible.formatters.text.message import MessageTransformer
from docsible.models.enhancement import Enhancement
from docsible.models.recommendation import Recommendation


class PositiveFormatter:
    """Format output with positive framing."""

    def __init__(self):
        self.transformer = MessageTransformer()
        self.start_time = time.time()

    def format_success(
        self,
        output_file: Path,
        complexity: ComplexityReport,
        recommendations: list[Recommendation],
    ) -> str:
        lines = []
        lines.extend(self._format_success_header(output_file))
        lines.append("")
        lines.extend(self._format_analysis(complexity))
        lines.append("")
        if recommendations:
            enhancements = [self.transformer.transform(rec) for rec in recommendations]
            lines.extend(self._format_enhancements(enhancements))
            lines.append("")
        else:
            lines.append("🎉 Excellent! No enhancement opportunities - role follows all best practices!")
            lines.append("")
        lines.extend(self._format_next_steps(output_file, complexity))
        return "\n".join(lines)

    def _format_success_header(self, output_file: Path) -> list[str]:
        elapsed = time.time() - self.start_time
        file_size = self._format_file_size(output_file)
        return [
            "✅ Documentation Generated Successfully!",
            "",
            f"📄 Output: {output_file}",
            f"⏱️  Generated in {elapsed:.2f}s",
            f"📏 Size: {file_size}",
        ]

    def _format_analysis(self, complexity: ComplexityReport) -> list[str]:
        lines = ["📊 Role Analysis:"]
        lines.append(f"   • {self._describe_complexity(complexity)}")
        lines.append(f"   • {self._describe_structure(complexity)}")
        lines.append(f"   • {self._describe_readiness(complexity)}")
        highlights = self._find_highlights(complexity)
        if highlights:
            lines.append("")
            lines.append("✨ Highlights:")
            for highlight in highlights:
                lines.append(f"   • {highlight}")
        return lines

    def _describe_complexity(self, report: ComplexityReport) -> str:
        category = report.category
        tasks = report.metrics.total_tasks
        if category == ComplexityCategory.SIMPLE:
            return f"Simple role ({tasks} tasks) - easy to maintain and understand"
        elif category == ComplexityCategory.MEDIUM:
            return f"Well-structured role ({tasks} tasks) - good balance of functionality"
        else:
            return f"Comprehensive role ({tasks} tasks) - handles complex workflows"

    def _describe_structure(self, report: ComplexityReport) -> str:
        has_handlers = report.metrics.handlers > 0
        has_meta = report.metrics.role_dependencies > 0
        has_modules = report.metrics.task_includes > 0 or report.metrics.role_includes > 0
        if has_handlers and has_meta and has_modules:
            return "Complete structure with handlers, metadata, and modular tasks"
        elif has_handlers and has_meta:
            return "Well-organized with handlers and metadata"
        elif has_handlers:
            return "Clean structure with handlers for service management"
        else:
            return "Minimal structure - easy to customize"

    def _describe_readiness(self, report: ComplexityReport) -> str:
        if report.category == ComplexityCategory.SIMPLE:
            return "Ready for immediate use"
        elif report.category == ComplexityCategory.MEDIUM:
            return "Production-ready with good practices"
        else:
            return "Comprehensive role ready for complex deployments"

    def _find_highlights(self, report: ComplexityReport) -> list[str]:
        highlights = []
        if report.metrics.conditional_tasks > 0 and report.metrics.total_tasks > 0:
            pct = (report.metrics.conditional_tasks / report.metrics.total_tasks) * 100
            highlights.append(f"Uses conditionals effectively ({pct:.0f}% of tasks)")
        if report.metrics.task_includes == 0 and report.metrics.role_includes == 0:
            highlights.append("Straightforward task flow - no nested includes")
        if 1 < report.metrics.task_files <= 5:
            highlights.append(f"Well-organized into {report.metrics.task_files} task files")
        if report.metrics.role_dependencies > 0:
            highlights.append(f"Leverages {report.metrics.role_dependencies} role dependencies")
        return highlights

    def _format_enhancements(self, enhancements: list[Enhancement]) -> list[str]:
        lines = ["💡 Enhancement Opportunities:"]
        by_priority: dict[int, list[Enhancement]] = {}
        for enh in enhancements:
            by_priority.setdefault(enh.priority, []).append(enh)
        for priority in sorted(by_priority.keys()):
            for enh in by_priority[priority]:
                lines.append(f"   • {enh.formatted_message}")
        return lines

    def _format_next_steps(self, output_file: Path, complexity: ComplexityReport) -> list[str]:
        lines = ["🎯 Next Steps:"]
        lines.append(f"   1. Review generated {output_file.name}")
        if complexity.category == ComplexityCategory.SIMPLE:
            lines.append("   2. Test with: ansible-playbook -i inventory playbook.yml")
            lines.append("   3. Share with your team")
        else:
            lines.append("   2. Add variable descriptions (if needed)")
            lines.append("   3. Test with: ansible-playbook --check playbook.yml")
            lines.append("   4. Generate graph with: docsible role --role . --graph")
        lines.append("")
        lines.append("📚 Learn more: https://docs.docsible.com/getting-started")
        return lines

    def _format_file_size(self, file_path: Path) -> str:
        if not file_path.exists():
            return "unknown"
        size_bytes: float = file_path.stat().st_size
        for unit in ["B", "KB", "MB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} GB"
