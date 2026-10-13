#!/usr/bin/env python3
import re
import sys
from typing import Any, Callable, Union

class MemoryGrep:
    """WALL-style memory pattern extractor: there's more than one way to query it."""
    
    def __init__(self, memories: list[str]):
        self.memories = memories
    
    def __call__(self, pattern: Union[str, dict, Callable]) -> list[dict]:
        """Duck-type the pattern - string, dict filter, or lambda."""
        if isinstance(pattern, str):
            return self._regex_extract(pattern)
        elif isinstance(pattern, dict):
            return self._dict_filter(pattern)
        elif callable(pattern):
            return self._lambda_filter(pattern)
        else:
            return self._fuzzy_match(str(pattern))
    
    def _regex_extract(self, regex: str) -> list[dict]:
        """Perl-style regex extraction with named groups."""
        compiled = re.compile(regex)
        results = []
        for mem in self.memories:
            if match := compiled.search(mem):
                results.append({
                    'raw': mem,
                    'groups': match.groups(),
                    'named': match.groupdict(),
                    'span': match.span()
                })
        return results
    
    def _dict_filter(self, filters: dict) -> list[dict]:
        """Filter by keyword presence (implicit AND)."""
        results = []
        for mem in self.memories:
            if all(re.search(rf'\b{k}\b.*{v}', mem, re.I) for k, v in filters.items()):
                results.append({'raw': mem, 'matched': filters})
        return results
    
    def _lambda_filter(self, func: Callable) -> list[dict]:
        """User-defined filter function."""
        results = []
        for mem in self.memories:
            if func(mem):
                results.append({'raw': mem, 'custom': True})
        return results
    
    def _fuzzy_match(self, keyword: str) -> list[dict]:
        """Fallback: case-insensitive substring."""
        return [{'raw': m, 'fuzzy': keyword} for m in self.memories if keyword.lower() in m.lower()]

if __name__ == '__main__':
    memories = sys.stdin.read().strip().split('\n') if not sys.stdin.isatty() else []
    grep = MemoryGrep(memories)
    
    # Demo: extract EVO versions
    results = grep(r'\[EVO #(?P<num>\d+) (?P<arch>\w+) v(?P<version>[\d.]+)')
    for r in results:
        if r['named']:
            print(f"{r['named']['arch']} #{r['named']['num']}: {r['named']['version']}")