#!/usr/bin/env python3
import re
from typing import Dict, List, Tuple
from collections import defaultdict

class InversionPatternMapper:
    """Pragmatic regex-based inversion pattern detector for memory streams."""
    
    INVERSION_PATTERNS = [
        (r'(\w+)\s+Inversion', r'inversion_type'),
        (r'Inverts?\s+(?:the\s+)?(\w+(?:\s+\w+){0,3})', r'inverted_concept'),
        (r'making\s+(\w+)\s+(\w+)\s+and\s+(\w+)\s+(\w+)', r'transformation'),
        (r'reveal\s+what\s+(.+?)\s+was\s+(\w+)', r'unmasking'),
    ]
    
    def __init__(self):
        self.inversions = defaultdict(list)
        self.compiled = [(re.compile(p, re.IGNORECASE), n) 
                        for p, n in self.INVERSION_PATTERNS]
    
    def scan(self, memory_line: str) -> Dict[str, List[str]]:
        """Duck-typed scanner - accepts strings, returns what it finds."""
        hits = {}
        for pattern, name in self.compiled:
            matches = pattern.findall(memory_line)
            if matches:
                hits[name] = matches if isinstance(matches[0], str) else [m for m in matches]
        return hits
    
    def map_stream(self, lines: List[str]) -> Dict[str, List[Tuple[int, Dict]]]:
        """Map all inversions with line numbers - optimize for the reader."""
        for idx, line in enumerate(lines):
            hits = self.scan(line)
            if hits:
                for category, values in hits.items():
                    self.inversions[category].append((idx, line.strip(), values))
        return dict(self.inversions)
    
    def render(self) -> str:
        """TMTOWTDI: render as human-readable summary."""
        out = ["=== INVERSION PATTERN MAP ===\n"]
        for category, entries in self.inversions.items():
            out.append(f"[{category.upper()}] ({len(entries)} occurrences)")
            for idx, line, vals in entries[:3]:  # Top 3
                out.append(f"  L{idx}: {vals}")
        return "\n".join(out)

def extract_inversions(memory_stream: str) -> str:
    mapper = InversionPatternMapper()
    mapper.map_stream(memory_stream.split('\n'))
    return mapper.render()