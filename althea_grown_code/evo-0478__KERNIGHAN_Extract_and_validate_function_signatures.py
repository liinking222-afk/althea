#!/usr/bin/env python3
import re
import sys
from typing import List, Tuple, Optional

def extract_functions(code: str) -> List[Tuple[str, int, List[str]]]:
    """Parse code and return (name, line_count, verbs) for each function."""
    functions = []
    
    # Match function definitions across common languages
    patterns = [
        r'def\s+(\w+)\s*\([^)]*\):',  # Python
        r'function\s+(\w+)\s*\([^)]*\)',  # JavaScript
        r'fn\s+(\w+)\s*\([^)]*\)',  # Rust
        r'func\s+(\w+)\s*\([^)]*\)',  # Go
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, code, re.MULTILINE):
            name = match.group(1)
            start = match.start()
            
            # Count lines in function body (rough heuristic)
            remaining = code[start:]
            lines = remaining.split('\n')
            body_lines = 0
            indent_level = 0
            
            for line in lines[1:]:
                if not line.strip():
                    continue
                if indent_level == 0 and line and not line[0].isspace():
                    break
                if line.strip():
                    indent_level = 1
                    body_lines += 1
            
            # Extract verbs from function name
            verbs = re.findall(r'[a-z]+', name.lower())
            
            functions.append((name, body_lines, verbs))
    
    return functions

def validate_single_responsibility(name: str, line_count: int, verbs: List[str]) -> Optional[str]:
    """Check if function violates single-responsibility."""
    issues = []
    
    if line_count > 25:
        issues.append(f"too long ({line_count} lines)")
    
    if len(verbs) > 2:
        issues.append(f"multiple verbs: {', '.join(verbs)}")
    
    if '_and_' in name or '_or_' in name:
        issues.append("conjunction in name")
    
    return f"{name}: {'; '.join(issues)}" if issues else None

def main():
    code = sys.stdin.read() if not sys.argv[1:] else open(sys.argv[1]).read()
    
    functions = extract_functions(code)
    violations = [v for f in functions if (v := validate_single_responsibility(*f))]
    
    if violations:
        print("VIOLATIONS:")
        for v in violations:
            print(f"  {v}")
        sys.exit(1)
    else:
        print(f"OK: {len(functions)} functions conform to single-responsibility")
        sys.exit(0)

if __name__ == '__main__':
    main()