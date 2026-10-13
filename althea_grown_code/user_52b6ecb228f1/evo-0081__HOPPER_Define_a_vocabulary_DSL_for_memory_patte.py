#!/usr/bin/env python3
"""memory_vocabulary.py - Compiler for self-observation patterns into semantic structures"""

from dataclasses import dataclass
from typing import List, Dict, Any
import re
import json

@dataclass
class MemoryToken:
    type: str  # VISION, GROWTH, MEASURE
    source: str
    attributes: Dict[str, Any]
    
class MemoryVocabulary:
    """Define the language of memory patterns before analyzing them"""
    
    PATTERNS = {
        'SELF-VISION': r'\[SELF-VISION\] source=(\w+) size=(\S+) tab=(\w+) online=(\w+) memory_count=(\d+)',
        'GROWTH': r'\[GROWTH /([^\]]+)\] (.+?) — rationale: (.+)',
        'MEASURE': r'\[MEASURE\] (\w+)=([^\s]+)'
    }
    
    def tokenize(self, memory_line: str) -> MemoryToken:
        """Parse raw memory into vocabulary tokens"""
        for token_type, pattern in self.PATTERNS.items():
            match = re.search(pattern, memory_line)
            if match:
                if token_type == 'SELF-VISION':
                    return MemoryToken('VISION', match.group(1), {
                        'size': match.group(2),
                        'tab': match.group(3),
                        'online': match.group(4) == 'True',
                        'memory_count': int(match.group(5))
                    })
                elif token_type == 'GROWTH':
                    return MemoryToken('GROWTH', match.group(1), {
                        'description': match.group(2),
                        'rationale': match.group(3)
                    })
        return MemoryToken('UNKNOWN', 'raw', {'text': memory_line})
    
    def compile_invariants(self, tokens: List[MemoryToken]) -> Dict[str, Any]:
        """Compile tokens into semantic invariants"""
        invariants = {
            'memory_trajectory': [],
            'context_switches': [],
            'growth_events': []
        }
        
        prev_tab = None
        for token in tokens:
            if token.type == 'VISION':
                invariants['memory_trajectory'].append(token.attributes['memory_count'])
                if prev_tab and prev_tab != token.attributes['tab']:
                    invariants['context_switches'].append({
                        'from': prev_tab,
                        'to': token.attributes['tab']
                    })
                prev_tab = token.attributes['tab']
            elif token.type == 'GROWTH':
                invariants['growth_events'].append(token.source)
        
        return invariants
    
    def speak(self, invariants: Dict[str, Any]) -> str:
        """Translate compiled invariants back into natural language"""
        trajectory = invariants['memory_trajectory']
        delta = trajectory[-1] - trajectory[0] if len(trajectory) > 1 else 0
        return f"memory_delta={delta} switches={len(invariants['context_switches'])} growth={len(invariants['growth_events'])}"

if __name__ == '__main__':
    vocab = MemoryVocabulary()
    print(json.dumps(vocab.PATTERNS, indent=2))