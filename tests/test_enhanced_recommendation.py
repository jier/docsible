from pathlib import Path
from docsible.analyzers.complexity_analyzer import analyze_role_complexity
from docsible.commands.document_role.core import build_role_info

def test_enhanced_recommendations():
    """Test that recommendations are specific and actionable."""
    
    # Build role info
    role_path = Path("tests/fixtures/complex_conditional_role")
    role_info = build_role_info(
        role_path=role_path,
        playbook_content=None,
        generate_graph=False,
        no_docsible=True,
        comments=False,
        task_line=False,
        belongs_to_collection=None,
        repository_url=None,
        repo_type=None,
        repo_branch=None,
    )
    
    # Analyze complexity
    report = analyze_role_complexity(role_info, include_patterns=False)
    
    print("=" * 60)
    print("ENHANCED RECOMMENDATIONS TEST")
    print("=" * 60)
    print(f"\nCategory: {report.category.value.upper()}")
    print(f"Total Tasks: {report.metrics.total_tasks}")
    print(f"Conditional Tasks: {report.metrics.conditional_tasks} ({report.metrics.conditional_percentage:.1f}%)")
    print("\nRecommendations:\n")
    
    for i, rec in enumerate(report.recommendations, 1):
        print(f"{i}. {rec}")
    
    print("\n" + "=" * 60)
    
    # Assertions
    assert len(report.recommendations) > 0, "Should generate recommendations"
    
    # Check for file-specific recommendations
    has_file_ref = any("tasks/" in rec for rec in report.recommendations)
    assert has_file_ref, "Should reference specific files"
    
    # Check for variable-specific recommendations
    has_var_ref = any("ansible_os_family" in rec or "environment" in rec for rec in report.recommendations)
    assert has_var_ref, "Should reference specific conditional variables"
    
    print("\n✅ All tests passed!")