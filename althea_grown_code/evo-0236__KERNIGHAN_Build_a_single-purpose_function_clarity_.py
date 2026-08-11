#!/usr/bin/env python3
"""Function clarity validator - ensures each function does ONE thing."""

import re
from typing import Tuple


def extract_verbs(docstring: str) -> list[str]:
    """Extract action verbs from docstring."""
    if not docstring:
        return []
    
    # Common verb patterns in docstrings
    patterns = [
        r'\b(creates?|builds?|validates?|extracts?|measures?|counts?|filters?|maps?|reduces?|transforms?|checks?|ensures?|proves?|generates?|processes?|reads?|writes?|returns?)\b',
        r'\b(and|then|also|additionally)\s+(\w+s?)\b'
    ]
    
    verbs = []
    lower = docstring.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, lower)
        verbs.extend([m if isinstance(m, str) else m[0] for m in matches])
    
    return list(set(verbs))


def measure_focus(function_code: str) -> Tuple[int, str]:
    """Count distinct purposes. Return (verb_count, assessment)."""
    lines = function_code.split('\n')
    docstring = ""
    
    # Extract docstring
    in_doc = False
    for line in lines:
        if '"""' in line or "'''" in line:
            if in_doc:
                docstring += line.split('"""')[0].split("'''")[0]
                break
            in_doc = True
            docstring += line.split('"""')[-1].split("'''")[-1] + " "
        elif in_doc:
            docstring += line.strip() + " "
    
    verbs = extract_verbs(docstring)
    count = len(verbs)
    
    if count == 0:
        return (0, "UNDOCUMENTED")
    elif count == 1:
        return (1, "CLEAR")
    elif count <= 3:
        return (count, "ACCEPTABLE")
    else:
        return (count, "UNFOCUSED")


def validate_clarity(code: str, threshold: int = 2) -> bool:
    """Check if code does ONE thing. Pipe-composable."""
    count, status = measure_focus(code)
    return count <= threshold and count > 0


if __name__ == "__main__":
    import sys
    code = sys.stdin.read() if not sys.stdin.isatty() else ""
    result = validate_clarity(code)
    sys.exit(0 if result else 1)