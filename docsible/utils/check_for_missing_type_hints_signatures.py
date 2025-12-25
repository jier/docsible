"""Check for missing type hints in function signatures."""
import ast
from pathlib import Path


def has_type_hints(node):
    """Check if a function has type hints."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return True
    
    # Check return annotation
    has_return = node.returns is not None
    
    # Check argument annotations (skip self, cls)
    args_with_hints = 0
    total_args = 0
    
    for arg in node.args.args:
        if arg.arg not in ('self', 'cls'):
            total_args += 1
            if arg.annotation is not None:
                args_with_hints += 1
    
    # If no args (besides self/cls), just check return
    if total_args == 0:
        return has_return
    
    # Otherwise, check if all args have hints
    return args_with_hints == total_args and has_return

def check_file(filepath):
    """Check a single file for type hints."""
    try:
        with open(filepath, 'r') as f:
            tree = ast.parse(f.read(), filepath)
        
        missing = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip private functions and test functions
                if node.name.startswith('_') or node.name.startswith('test_'):
                    continue
                
                if not has_type_hints(node):
                    missing.append((node.name, node.lineno))
        
        return missing
    except Exception as e:
        return None 

if __name__ == '__main__':
    base_path = Path().parent
    
    files_without_hints = {}
    
    for py_file in base_path.rglob('*.py'):
        if '__pycache__' in str(py_file) or 'tests' in str(py_file):
            continue
        
        missing = check_file(py_file)
        if missing:
            files_without_hints[str(py_file.relative_to(base_path))] = missing
    
    if files_without_hints:
        for filepath, funcs in sorted(files_without_hints.items()):
            print(f"\n{filepath}:")
            for func_name, lineno in funcs[:5]:  # Show first 5
                print(f"  - {func_name}() at line {lineno}")
            if len(funcs) > 5:
                print(f"  ... and {len(funcs) - 5} more")