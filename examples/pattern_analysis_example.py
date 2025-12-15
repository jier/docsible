#!/usr/bin/env python3
"""Example: Using the Pattern Analyzer to identify anti-patterns.

This script demonstrates how to use the pattern analysis system
to detect issues in Ansible roles and generate improvement suggestions.
"""

from pathlib import Path
from docsible.analyzers.patterns import analyze_role_patterns, PatternAnalyzer
from docsible.analyzers.patterns.detectors import SecurityDetector, DuplicationDetector
from docsible.parsers.role_parser import parse_role


def example_basic_analysis():
    """Example 1: Basic pattern analysis."""
    print("=" * 70)
    print("Example 1: Basic Pattern Analysis")
    print("=" * 70)

    # Parse role (using test fixture)
    role_path = Path(__file__).parent.parent / "tests" / "fixtures" / "simple_role"
    role_info = parse_role(str(role_path))

    # Analyze patterns
    report = analyze_role_patterns(role_info)

    # Print summary
    print(f"\n📊 Analysis Results:")
    print(f"   Overall Health Score: {report.overall_health_score:.1f}/100")
    print(f"   Total Patterns Found: {report.total_patterns}")
    print(f"   - Critical:  {report.by_severity.get('critical', 0)}")
    print(f"   - Warnings:  {report.by_severity.get('warning', 0)}")
    print(f"   - Info:      {report.by_severity.get('info', 0)}")

    # Show breakdown by category
    print(f"\n📂 By Category:")
    for category, count in sorted(report.by_category.items()):
        print(f"   - {category:15s}: {count}")

    # Show first few suggestions
    if report.suggestions:
        print(f"\n💡 Sample Suggestions:")
        for suggestion in report.suggestions[:3]:
            print(f"\n   {suggestion.severity.upper()}: {suggestion.description}")
            print(f"   Pattern: {suggestion.pattern}")
            print(f"   Impact: {suggestion.impact}")
            print(f"   Files: {', '.join(suggestion.affected_files)}")


def example_filtered_analysis():
    """Example 2: Filtered analysis by severity and category."""
    print("\n" + "=" * 70)
    print("Example 2: Filtered Analysis")
    print("=" * 70)

    role_path = Path(__file__).parent.parent / "tests" / "fixtures" / "simple_role"
    role_info = parse_role(str(role_path))

    report = analyze_role_patterns(role_info)

    # Show only critical issues
    critical = [s for s in report.suggestions if s.severity == 'critical']

    if critical:
        print(f"\n🚨 Critical Issues ({len(critical)}):")
        for issue in critical:
            print(f"\n   {issue.description}")
            print(f"   How to fix: {issue.suggestion[:200]}...")
    else:
        print("\n✅ No critical issues found!")

    # Show security issues
    security = [s for s in report.suggestions if s.category == 'security']

    if security:
        print(f"\n🔒 Security Issues ({len(security)}):")
        for issue in security:
            print(f"\n   {issue.description}")
            print(f"   Confidence: {issue.confidence * 100:.0f}%")
    else:
        print("\n✅ No security issues found!")


def example_custom_detectors():
    """Example 3: Using specific detectors only."""
    print("\n" + "=" * 70)
    print("Example 3: Custom Detector Selection")
    print("=" * 70)

    role_path = Path(__file__).parent.parent / "tests" / "fixtures" / "simple_role"
    role_info = parse_role(str(role_path))

    # Only run security and duplication checks
    print("\n🔍 Running security and duplication detectors only...")
    analyzer = PatternAnalyzer(
        enabled_detectors=[SecurityDetector, DuplicationDetector],
        min_confidence=0.7
    )

    report = analyzer.analyze(role_info)

    print(f"\n📊 Focused Analysis Results:")
    print(f"   Patterns Found: {report.total_patterns}")

    for suggestion in report.suggestions:
        print(f"\n   [{suggestion.category.upper()}] {suggestion.description}")


def example_high_confidence_only():
    """Example 4: High-confidence patterns only."""
    print("\n" + "=" * 70)
    print("Example 4: High-Confidence Patterns Only (≥85%)")
    print("=" * 70)

    role_path = Path(__file__).parent.parent / "tests" / "fixtures" / "simple_role"
    role_info = parse_role(str(role_path))

    # Only show high-confidence patterns
    analyzer = PatternAnalyzer(min_confidence=0.85)
    report = analyzer.analyze(role_info)

    print(f"\n📊 High-Confidence Results:")
    print(f"   Patterns Found: {report.total_patterns}")

    if report.suggestions:
        print(f"\n💯 High-Confidence Suggestions:")
        for suggestion in report.suggestions:
            print(f"\n   {suggestion.description}")
            print(f"   Confidence: {suggestion.confidence * 100:.0f}%")
            print(f"   Impact: {suggestion.impact}")
    else:
        print("\n✅ No high-confidence issues found!")


def example_export_results():
    """Example 5: Export results to JSON."""
    print("\n" + "=" * 70)
    print("Example 5: Export Results")
    print("=" * 70)

    role_path = Path(__file__).parent.parent / "tests" / "fixtures" / "simple_role"
    role_info = parse_role(str(role_path))

    report = analyze_role_patterns(role_info)

    # Export to JSON
    import json
    output_file = "/tmp/pattern_analysis_report.json"

    report_dict = report.model_dump()
    with open(output_file, 'w') as f:
        json.dump(report_dict, f, indent=2)

    print(f"\n💾 Exported to: {output_file}")
    print(f"   Size: {Path(output_file).stat().st_size} bytes")

    # Show sample of exported data
    print(f"\n📄 Sample Export Data:")
    sample = {
        "total_patterns": report_dict["total_patterns"],
        "overall_health_score": report_dict["overall_health_score"],
        "by_severity": report_dict["by_severity"],
        "by_category": report_dict["by_category"]
    }
    print(json.dumps(sample, indent=2))


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("PATTERN ANALYZER EXAMPLES")
    print("=" * 70)

    try:
        example_basic_analysis()
        example_filtered_analysis()
        example_custom_detectors()
        example_high_confidence_only()
        example_export_results()

        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
