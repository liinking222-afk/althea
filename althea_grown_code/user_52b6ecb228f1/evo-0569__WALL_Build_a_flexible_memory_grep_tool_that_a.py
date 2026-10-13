#!/usr/bin/env python3
"""memgrep - flexible memory search with WALL philosophy: TIMTOWTDI"""
import sys
import re
import json
from typing import Iterator, Dict, Any

def search_memories(pattern: str, memories: Iterator[str], 
                   use_regex: bool = True, 
                   case_sensitive: bool = False) -> Iterator[Dict[str, Any]]:
    """Duck-typed search - works with any iterable of strings"""
    flags = 0 if case_sensitive else re.IGNORECASE
    
    if use_regex:
        try:
            compiled = re.compile(pattern, flags)
            matcher = lambda text: compiled.search(text)
        except re.error:
            # Fallback gracefully if regex is malformed
            matcher = lambda text: pattern.lower() in text.lower()
    else:
        if case_sensitive:
            matcher = lambda text: pattern in text
        else:
            matcher = lambda text: pattern.lower() in text.lower()
    
    for line in memories:
        line = line.rstrip('\n')
        if not line:
            continue
        if matcher(line):
            yield {"matched": line, "pattern": pattern}

def format_output(matches: Iterator[Dict[str, Any]], fmt: str = "text") -> None:
    """Multiple output formats - optimize for writer AND reader"""
    if fmt == "json":
        for match in matches:
            print(json.dumps(match))
    elif fmt == "count":
        print(sum(1 for _ in matches))
    elif fmt == "compact":
        for match in matches:
            # Extract key content using simple heuristics
            line = match["matched"]
            if "]" in line:
                print(line.split("]", 1)[1].strip())
            else:
                print(line[:80])
    else:  # text - default human-readable
        for match in matches:
            print(match["matched"])

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="WALL-style memory grep")
    p.add_argument("pattern", help="Search pattern (regex or plain)")
    p.add_argument("-F", "--fixed", action="store_true", help="Fixed string, not regex")
    p.add_argument("-i", "--ignore-case", action="store_true", default=True)
    p.add_argument("-f", "--format", choices=["text", "json", "count", "compact"], 
                   default="text", help="Output format")
    args = p.parse_args()
    
    matches = search_memories(
        args.pattern, 
        sys.stdin,
        use_regex=not args.fixed,
        case_sensitive=not args.ignore_case
    )
    
    format_output(matches, args.format)