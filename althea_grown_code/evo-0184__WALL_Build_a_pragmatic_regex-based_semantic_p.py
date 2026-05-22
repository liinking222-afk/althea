#!/usr/bin/env python3
import re
from typing import List, Dict, Any, Union, Callable
from dataclasses import dataclass

@dataclass
class PatternMatch:
    content: str
    score: float
    captures: Dict[str, str]
    
class FlexiMatcher:
    """WALL-style semantic pattern matcher: multiple ways, reader-optimized"""
    
    def __init__(self):
        self.patterns: List[tuple[re.Pattern, Callable]] = []
    
    def add(self, *patterns: Union[str, re.Pattern], weight: float = 1.0):
        """Duck-typed pattern addition - strings or compiled patterns"""
        for p in patterns:
            compiled = p if isinstance(p, re.Pattern) else re.compile(p, re.IGNORECASE | re.MULTILINE)
            self.patterns.append((compiled, lambda m, w=weight: w * len(m.group(0))))
        return self
    
    def match_any(self, text: str, min_score: float = 0.0) -> List[PatternMatch]:
        """There's more than one way to match it"""
        results = []
        for pattern, scorer in self.patterns:
            for match in pattern.finditer(text):
                score = scorer(match)
                if score >= min_score:
                    results.append(PatternMatch(
                        content=match.group(0),
                        score=score,
                        captures=match.groupdict()
                    ))
        return sorted(results, key=lambda m: m.score, reverse=True)
    
    def search_memories(self, memories: List[str], query_patterns: List[str]) -> Dict[str, List[PatternMatch]]:
        """Pragmatic glue for searching Althea's memory logs"""
        matcher = FlexiMatcher()
        for qp in query_patterns:
            matcher.add(qp)
        
        return {
            mem: matcher.match_any(mem, min_score=1.0)
            for mem in memories
            if matcher.match_any(mem, min_score=1.0)
        }
    
    def pipe(self, other: 'FlexiMatcher') -> 'FlexiMatcher':
        """Composable matcher chains"""
        combined = FlexiMatcher()
        combined.patterns = self.patterns + other.patterns
        return combined

if __name__ == "__main__":
    fm = FlexiMatcher()
    fm.add(r"semantic\s+\w+", r"perception", r"\bevo\b.*#\d+", weight=2.0)
    
    test = "EVO #183 THOMPSON semantic centroid perception module"
    matches = fm.match_any(test)
    for m in matches:
        print(f"{m.score:.1f}: {m.content}")