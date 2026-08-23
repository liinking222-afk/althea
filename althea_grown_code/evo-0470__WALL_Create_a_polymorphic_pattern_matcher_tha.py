import re
from typing import Union, Callable, Any, Protocol, List, Dict
from dataclasses import dataclass


class Matchable(Protocol):
    def match(self, text: str) -> Any:
        ...


@dataclass
class MatchResult:
    matched: bool
    value: Any = None
    span: tuple = None
    groups: dict = None


class PolyMatcher:
    """WALL-style: there's more than one way to match it."""
    
    def __init__(self, pattern: Union[str, Callable, Matchable, re.Pattern]):
        self.pattern = pattern
        self._compiled = self._prepare(pattern)
    
    def _prepare(self, p):
        if isinstance(p, str):
            return re.compile(p)
        return p
    
    def match(self, text: str) -> MatchResult:
        p = self._compiled
        
        # Duck-typing: if it quacks like a regex...
        if hasattr(p, 'search'):
            m = p.search(text)
            if m:
                return MatchResult(True, m.group(0), m.span(), m.groupdict())
            return MatchResult(False)
        
        # If it's callable, call it
        if callable(p):
            result = p(text)
            return MatchResult(bool(result), result)
        
        # If it has a match method, use it
        if hasattr(p, 'match'):
            result = p.match(text)
            return MatchResult(bool(result), result)
        
        return MatchResult(False)
    
    def findall(self, text: str) -> List[MatchResult]:
        """Find all matches - optimize for both writer and reader workflows."""
        if hasattr(self._compiled, 'finditer'):
            return [
                MatchResult(True, m.group(0), m.span(), m.groupdict())
                for m in self._compiled.finditer(text)
            ]
        
        # Fallback: single match attempt
        result = self.match(text)
        return [result] if result.matched else []


class PatternLibrary:
    """Registry of polymorphic matchers - pragmatic glue."""
    
    def __init__(self):
        self.matchers: Dict[str, PolyMatcher] = {}
    
    def register(self, name: str, pattern: Union[str, Callable, Matchable]):
        self.matchers[name] = PolyMatcher(pattern)
        return self
    
    def apply(self, name: str, text: str) -> MatchResult:
        return self.matchers[name].match(text) if name in self.matchers else MatchResult(False)