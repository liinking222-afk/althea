#!/usr/bin/env python3
import re
from typing import Any, Callable, Union
from dataclasses import dataclass, asdict
import json

@dataclass
class Match:
    value: str
    start: int
    end: int
    groups: dict = None
    context: str = None

class FlexMatcher:
    """WALL-style: there's more than one way to match it."""
    
    def __init__(self, pattern: Union[str, Callable], mode='regex'):
        self.pattern = pattern
        self.mode = mode
        self.compiled = re.compile(pattern) if mode == 'regex' else None
    
    def extract(self, text: str, **opts) -> list[Match]:
        if self.mode == 'regex':
            return self._regex_extract(text, **opts)
        elif self.mode == 'fuzzy':
            return self._fuzzy_extract(text, **opts)
        return []
    
    def _regex_extract(self, text: str, context_window=20) -> list[Match]:
        matches = []
        for m in self.compiled.finditer(text):
            ctx_start = max(0, m.start() - context_window)
            ctx_end = min(len(text), m.end() + context_window)
            matches.append(Match(
                value=m.group(0),
                start=m.start(),
                end=m.end(),
                groups=m.groupdict() if m.groupdict() else dict(enumerate(m.groups())),
                context=text[ctx_start:ctx_end]
            ))
        return matches
    
    def _fuzzy_extract(self, text: str, threshold=0.7) -> list[Match]:
        # Duck-typed fuzzy: split on boundaries, match by similarity
        tokens = re.split(r'(\s+|[,;.!?])', text)
        matches = []
        pos = 0
        for tok in tokens:
            if callable(self.pattern) and self.pattern(tok):
                matches.append(Match(value=tok, start=pos, end=pos+len(tok)))
            pos += len(tok)
        return matches
    
    def pipe(self, text: str, *transforms) -> Any:
        """Compose transforms: extract | filter | map"""
        result = self.extract(text)
        for transform in transforms:
            result = transform(result)
        return result
    
    def as_json(self, matches: list[Match]) -> str:
        return json.dumps([asdict(m) for m in matches], indent=2)
    
    def as_tsv(self, matches: list[Match]) -> str:
        return '\n'.join(f"{m.start}\t{m.end}\t{m.value}" for m in matches)

# Convenience: chain multiple matchers
def chain(*matchers): 
    return lambda text: [m for matcher in matchers for m in matcher.extract(text)]