#!/usr/bin/env python3
import re
from collections import Counter
from typing import List, Dict

def extract_tokens(memory_line: str) -> List[str]:
    """Pull concept names from bracketed memory entries."""
    patterns = [
        r'\[GROWTH /autonomous-([^\]]+)\]',
        r'\[EVO #\d+ \w+ [^\]]*\] ([^—]+)',
        r'\[AUTOSYNTH /autonomous-([^\]]+)\]',
        r'\[IMAGINED\] ([^,\n]+)'
    ]
    tokens = []
    for pattern in patterns:
        matches = re.findall(pattern, memory_line)
        tokens.extend(matches)
    return [t.strip().lower().replace('-', '_') for t in tokens]

def count_concepts(memories: List[str]) -> Dict[str, int]:
    """Count concept frequency across all memories."""
    counter = Counter()
    for memory in memories:
        tokens = extract_tokens(memory)
        counter.update(tokens)
    return dict(counter.most_common())

def filter_recurring(concept_counts: Dict[str, int], threshold: int = 2) -> Dict[str, int]:
    """Return only concepts that recur above threshold."""
    return {k: v for k, v in concept_counts.items() if v >= threshold}

def format_report(recurring: Dict[str, int]) -> str:
    """Format as name:count pipe-delimited."""
    return ' | '.join(f"{name}:{count}" for name, count in recurring.items())

if __name__ == '__main__':
    import sys
    memories = sys.stdin.readlines()
    concepts = count_concepts(memories)
    recurring = filter_recurring(concepts)
    print(format_report(recurring))