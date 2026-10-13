#!/usr/bin/env python3
import sys
import re

def extract_signatures(text):
    """Extract function signatures as plain text lines."""
    patterns = [
        (r'^\s*def\s+(\w+)\s*\(([^)]*)\)', 'python'),
        (r'^\s*function\s+(\w+)\s*\(([^)]*)\)', 'javascript'),
        (r'^\s*const\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>', 'javascript'),
        (r'^\s*fn\s+(\w+)\s*\(([^)]*)\)', 'rust'),
        (r'^\s*func\s+(\w+)\s*\(([^)]*)\)', 'go'),
        (r'^\s*(?:public|private|protected)?\s*(\w+)\s*\(([^)]*)\)\s*\{', 'java'),
    ]
    
    for line in text.split('\n'):
        for pattern, lang in patterns:
            match = re.search(pattern, line)
            if match:
                name = match.group(1)
                params = match.group(2).strip()
                print(f"{name}|{params}|{lang}")
                break

def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    
    extract_signatures(text)

if __name__ == '__main__':
    main()