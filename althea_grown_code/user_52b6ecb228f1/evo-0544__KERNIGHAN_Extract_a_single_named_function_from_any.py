#!/usr/bin/env python3
import re
import sys
from pathlib import Path

def extract_function(source_code, function_name):
    """Extract a single function definition from source code."""
    lines = source_code.split('\n')
    result = []
    in_function = False
    base_indent = None
    
    for line in lines:
        if re.match(rf'^(async\s+)?def\s+{re.escape(function_name)}\s*\(', line):
            in_function = True
            base_indent = len(line) - len(line.lstrip())
            result.append(line)
        elif in_function:
            if line.strip() == '':
                result.append(line)
            else:
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= base_indent and line.strip():
                    break
                result.append(line)
    
    return '\n'.join(result) if result else None

def main():
    if len(sys.argv) != 3:
        print("Usage: extract_function.py <source_file> <function_name>")
        sys.exit(1)
    
    source_file = Path(sys.argv[1])
    function_name = sys.argv[2]
    
    if not source_file.exists():
        print(f"Error: {source_file} not found", file=sys.stderr)
        sys.exit(1)
    
    source_code = source_file.read_text()
    extracted = extract_function(source_code, function_name)
    
    if extracted:
        output_file = Path(f"{function_name}.py")
        output_file.write_text(extracted + '\n')
        print(f"{output_file}")
    else:
        print(f"Error: function '{function_name}' not found", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()