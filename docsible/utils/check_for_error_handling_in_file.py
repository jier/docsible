"""Check for error handling patterns."""
import ast
from pathlib import Path


def check_file(filepath):
    """Check error handling in a file."""
    try:
        with open(filepath) as f:
            content = f.read()
            tree = ast.parse(content, filepath)
        
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # Check if handler has logging
                for handler in node.handlers:
                    handler_body = ast.unparse(handler.body) if hasattr(ast, 'unparse') else str(handler.body)
                    
                    # Check if using print, click.echo, or logger
                    has_logging = any(keyword in handler_body for keyword in [
                        'logger.', 'logging.', 'click.echo', 'click.secho'
                    ])
                    
                    # Check if silently passing
                    is_silent_pass = (len(handler.body) == 1 and 
                                     isinstance(handler.body[0], ast.Pass))
                    
                    if not has_logging and not is_silent_pass:
                        exc_type = handler.type.id if hasattr(handler.type, 'id') else 'Exception'
                        issues.append((node.lineno, exc_type, 'no_logging'))
        
        return issues
    except Exception as e:
        return None

if __name__ == '__main__':
    base_path = Path().parent
    
    files_with_issues = {}
    
    for py_file in base_path.rglob('*.py'):
        if '__pycache__' in str(py_file) or 'tests' in str(py_file):
            continue
        
        issues = check_file(py_file)
        if issues:
            files_with_issues[str(py_file.relative_to(base_path))] = issues
    
    if files_with_issues:
        for filepath, issues in sorted(files_with_issues.items()):
            if len(issues) > 0:
                print(f"\n{filepath}: {len(issues)} unlogged exceptions")