#!/usr/bin/env python3
import re
from typing import List, Dict, Any, Optional

class MemoryGrep:
    """Pragmatic regex-powered memory query - TIMTOWTDI for evolution search."""
    
    def __init__(self, memory_stream: List[str]):
        self.memories = memory_stream
        self.last_matches = []
    
    def search(self, pattern: str, flags: str = "") -> 'MemoryGrep':
        """Grep memories with Perl-style regex. Flags: i=ignore case, m=multiline."""
        re_flags = 0
        if 'i' in flags: re_flags |= re.IGNORECASE
        if 'm' in flags: re_flags |= re.MULTILINE
        
        compiled = re.compile(pattern, re_flags)
        self.last_matches = [m for m in self.memories if compiled.search(m)]
        return self
    
    def extract(self, pattern: str, group: int = 0) -> List[str]:
        """Extract capture groups from last search results."""
        compiled = re.compile(pattern)
        results = []
        for memory in self.last_matches:
            match = compiled.search(memory)
            if match:
                results.append(match.group(group) if group <= len(match.groups()) else match.group(0))
        return results
    
    def substitute(self, pattern: str, replacement: str) -> List[str]:
        """Perl-style s/// on matched memories."""
        return [re.sub(pattern, replacement, m) for m in self.last_matches]
    
    def split_on(self, delimiter: str = r'\s+') -> List[List[str]]:
        """Split matched memories into tokens."""
        return [re.split(delimiter, m) for m in self.last_matches]
    
    def match_dict(self, pattern: str) -> List[Dict[str, str]]:
        """Extract named capture groups as dicts."""
        compiled = re.compile(pattern)
        results = []
        for memory in self.last_matches:
            match = compiled.search(memory)
            if match:
                results.append(match.groupdict())
        return results
    
    def count(self) -> int:
        return len(self.last_matches)
    
    def get(self) -> List[str]:
        return self.last_matches
    
    def chain(self, pattern: str, flags: str = "") -> 'MemoryGrep':
        """Pipe pattern: filter last_matches further."""
        return MemoryGrep(self.last_matches).search(pattern, flags)

# Usage: grep = MemoryGrep(memories).search(r'EVO.*THOMPSON').extract(r'v(\d+\.\d+\.\d+)', 1)