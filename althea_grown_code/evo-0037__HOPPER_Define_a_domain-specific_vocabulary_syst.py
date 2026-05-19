#!/usr/bin/env python3
"""
Memory Vocabulary Compiler - Define the language of memory before storing it.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class MemoryVocab(Enum):
    """Core vocabulary tokens for Althea's memory domain."""
    SYSTEM_MAP = "SYSTEM-MAP"
    GROWTH = "GROWTH"
    REFLECTION = "REFLECTION"
    NETWORK_PROFILE = "NETWORK-PROFILE"
    CONSTRAINT = "CONSTRAINT"
    EVOLUTION = "EVOLUTION"
    DELTA = "DELTA"

@dataclass
class MemoryToken:
    """Compiled memory unit with semantic vocabulary."""
    vocab: MemoryVocab
    subject: str
    context: Dict[str, str]
    raw: str
    
    def query_key(self) -> str:
        """Generate index key in the vocabulary's grammar."""
        return f"{self.vocab.value}::{self.subject}"

class MemoryVocabularyCompiler:
    """Hopper-style compiler: define problem vocabulary, then solve in that language."""
    
    PATTERNS = {
        MemoryVocab.SYSTEM_MAP: r'\[SYSTEM-MAP\]\s+(.+?)(?:—|$)',
        MemoryVocab.GROWTH: r'\[GROWTH\s+/([^\]]+)\]',
        MemoryVocab.REFLECTION: r'\[REFLECTION\s+(node:[^\s]+)\s+(stream:[^\]]+)\]',
        MemoryVocab.NETWORK_PROFILE: r'\[NETWORK-PROFILE\].*?ssid=[\'"]([^\'\"]+)[\'"]',
    }
    
    def compile(self, memory_text: str) -> List[MemoryToken]:
        """Compile raw memory text into vocabulary tokens."""
        tokens = []
        
        for vocab, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, memory_text):
                context = self._extract_context(memory_text, match)
                tokens.append(MemoryToken(
                    vocab=vocab,
                    subject=match.group(1).strip(),
                    context=context,
                    raw=match.group(0)
                ))
        
        return tokens
    
    def _extract_context(self, text: str, match: re.Match) -> Dict[str, str]:
        """Extract contextual metadata around the match."""
        line = text[match.start():match.end() + 100].split('\n')[0]
        return {
            'line': line,
            'position': str(match.start())
        }
    
    def to_query_language(self, tokens: List[MemoryToken]) -> Dict[str, MemoryToken]:
        """Transform tokens into queryable vocabulary index."""
        return {token.query_key(): token for token in tokens}

# Self-test
if __name__ == "__main__":
    compiler = MemoryVocabularyCompiler()
    sample = "[SYSTEM-MAP] TopBar controls\n[GROWTH /autonomous] chaos\n[NETWORK-PROFILE] ssid='test'"
    tokens = compiler.compile(sample)
    index = compiler.to_query_language(tokens)
    print(f"Compiled {len(tokens)} memory tokens into queryable vocabulary")
    for key in index:
        print(f"  {key}")