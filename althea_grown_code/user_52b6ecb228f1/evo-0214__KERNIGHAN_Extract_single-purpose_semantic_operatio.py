#!/usr/bin/env python3
"""semantic_debris_extractor.py - Extract residual pattern fragments from context"""

import re
from typing import Iterator, NamedTuple


class SemanticDebris(NamedTuple):
    """Single fragment of incomplete semantic material."""
    position: int
    content: str
    confidence: float


def extract_debris(text: str, min_confidence: float = 0.3) -> Iterator[SemanticDebris]:
    """Yield incomplete semantic fragments from text."""
    for match in re.finditer(r'(?:—\s*(?:rationale|because|since):?\s*)([^.—]+)', text, re.IGNORECASE):
        yield SemanticDebris(
            position=match.start(),
            content=match.group(1).strip(),
            confidence=0.7
        )
    
    for match in re.finditer(r'\b(?:partial|incomplete|residual|collapsed)\s+(\w+(?:\s+\w+){0,4})', text, re.IGNORECASE):
        yield SemanticDebris(
            position=match.start(),
            content=match.group(1).strip(),
            confidence=0.4
        )
    
    for match in re.finditer(r'\.{3,}|—$|:\s*$', text, re.MULTILINE):
        context_start = max(0, match.start() - 50)
        context = text[context_start:match.start()].strip()
        if context:
            yield SemanticDebris(
                position=match.start(),
                content=context,
                confidence=0.5
            )


def filter_by_confidence(debris: Iterator[SemanticDebris], threshold: float) -> Iterator[SemanticDebris]:
    """Yield only debris meeting confidence threshold."""
    return (d for d in debris if d.confidence >= threshold)


def format_debris(debris: SemanticDebris) -> str:
    """Format single debris fragment for output."""
    return f"@{debris.position} [{debris.confidence:.2f}] {debris.content}"


if __name__ == "__main__":
    import sys
    text = sys.stdin.read()
    for d in filter_by_confidence(extract_debris(text), 0.3):
        print(format_debris(d))