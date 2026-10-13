#!/usr/bin/env python3
"""
ALTHEA MODULE: pattern_resonance_matcher
Pragmatic regex-based pattern surfacing across memory fragments.
There's more than one way to find connections.
"""

import re
from typing import Any, List, Dict, Optional
from collections import defaultdict

class PatternResonanceMatcher:
    def __init__(self):
        self.pattern_cache = defaultdict(list)
        self.fuzzy_threshold = 0.6
    
    def add_fragment(self, fragment: Any, source: str = "unknown"):
        """Duck-type over any fragment - str, dict, list, or object."""
        text = self._stringify(fragment)
        self.pattern_cache[source].append(text)
    
    def _stringify(self, obj: Any) -> str:
        """TIMTOWTDI stringification."""
        if isinstance(obj, str):
            return obj
        elif isinstance(obj, dict):
            return " ".join(f"{k}:{v}" for k, v in obj.items())
        elif isinstance(obj, (list, tuple)):
            return " ".join(str(x) for x in obj)
        else:
            return str(obj)
    
    def find_resonances(self, pattern: str, fuzzy: bool = True) -> Dict[str, List[str]]:
        """Search for pattern across all fragments with optional fuzzy matching."""
        if fuzzy:
            pattern = self._fuzzify_pattern(pattern)
        
        regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        matches = defaultdict(list)
        
        for source, fragments in self.pattern_cache.items():
            for fragment in fragments:
                if regex.search(fragment):
                    matches[source].append(fragment)
        
        return dict(matches)
    
    def _fuzzify_pattern(self, pattern: str) -> str:
        """Convert rigid pattern to fuzzy regex - insert optional chars."""
        return ".*?".join(re.escape(char) for char in pattern)
    
    def extract_operators(self, text: str) -> List[str]:
        """Extract Althea-style operators: /path, #tag, @mention."""
        operators = []
        operators.extend(re.findall(r'/[\w-]+(?:/[\w-]+)*', text))
        operators.extend(re.findall(r'#[\w-]+', text))
        operators.extend(re.findall(r'@[\w-]+', text))
        return operators
    
    def cross_pollinate(self, min_overlap: int = 2) -> Dict[str, List[str]]:
        """Find sources sharing multiple operator patterns."""
        source_ops = {}
        for source, fragments in self.pattern_cache.items():
            ops = set()
            for frag in fragments:
                ops.update(self.extract_operators(frag))
            source_ops[source] = ops
        
        resonances = defaultdict(list)
        sources = list(source_ops.keys())
        for i, src1 in enumerate(sources):
            for src2 in sources[i+1:]:
                overlap = source_ops[src1] & source_ops[src2]
                if len(overlap) >= min_overlap:
                    resonances[f"{src1}↔{src2}"] = list(overlap)
        
        return dict(resonances)

matcher = PatternResonanceMatcher()