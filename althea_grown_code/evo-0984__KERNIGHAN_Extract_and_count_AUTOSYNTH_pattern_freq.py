#!/usr/bin/env python3
import re
from collections import Counter
from typing import List, Tuple

def extract_pattern(line: str) -> str or None:
    """Extract pattern name from AUTOSYNTH log line."""
    match = re.search(r'\[AUTOSYNTH /autonomous-([a-z-]+)-\d+\]', line)
    return match.group(1) if match else None

def count_patterns(lines: List[str]) -> Counter:
    """Count frequency of each pattern."""
    patterns = [extract_pattern(line) for line in lines]
    return Counter(p for p in patterns if p)

def rank_patterns(lines: List[str]) -> List[Tuple[str, int]]:
    """Return patterns ranked by frequency."""
    counts = count_patterns(lines)
    return counts.most_common()

def format_report(ranked: List[Tuple[str, int]]) -> str:
    """Format ranking as readable report."""
    lines = ["PATTERN DEMAND REPORT"]
    for pattern, count in ranked:
        lines.append(f"{pattern}: {count}")
    return "\n".join(lines)

def analyze_memory(memory_text: str) -> str:
    """Main: analyze memory and return demand report."""
    lines = memory_text.strip().split("\n")
    ranked = rank_patterns(lines)
    return format_report(ranked)

if __name__ == "__main__":
    import sys
    memory = sys.stdin.read()
    print(analyze_memory(memory))