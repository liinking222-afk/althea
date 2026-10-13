#!/usr/bin/env python3
import re
import sys
from typing import List, Tuple

def read_code(filepath: str) -> str:
    with open(filepath, 'r') as f:
        return f.read()

def find_functions(code: str) -> List[Tuple[str, str]]:
    pattern = r'def\s+(\w+)\s*\([^)]*\):[^:]*?(?=\ndef\s|\nclass\s|\Z)'
    return re.findall(pattern, code, re.DOTALL)

def count_concerns(func_body: str) -> int:
    concerns = 0
    if re.search(r'\bopen\(|\.read\(|\.write\(', func_body):
        concerns += 1
    if re.search(r'\bif\b.*\belse\b|\bfor\b|\bwhile\b', func_body):
        concerns += 1
    if re.search(r'\.append\(|\.extend\(|\+=', func_body):
        concerns += 1
    if re.search(r'print\(|log\.|logger\.', func_body):
        concerns += 1
    if re.search(r'return\b', func_body):
        concerns += 1
    return concerns

def suggest_split(name: str, body: str, concern_count: int) -> str:
    if concern_count <= 2:
        return ""
    
    suggestions = []
    if re.search(r'\bopen\(|\.read\(', body):
        suggestions.append(f"load_{name}_data")
    if re.search(r'\.write\(', body):
        suggestions.append(f"save_{name}_result")
    if re.search(r'\bfor\b.*in\b', body):
        suggestions.append(f"process_{name}_item")
    
    return f"{name} ({concern_count} concerns) → {' | '.join(suggestions)}"

def main():
    if len(sys.argv) < 2:
        print("Usage: split_concerns.py <filepath>")
        sys.exit(1)
    
    code = read_code(sys.argv[1])
    functions = find_functions(code)
    
    for name, body in functions:
        concerns = count_concerns(body)
        suggestion = suggest_split(name, body, concerns)
        if suggestion:
            print(suggestion)

if __name__ == "__main__":
    main()