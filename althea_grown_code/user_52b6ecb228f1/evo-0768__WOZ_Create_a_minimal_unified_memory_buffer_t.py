#!/usr/bin/env python3
"""
ALTHEA MODULE: memory_compressor.py
Woz principle: Every byte counts. Compress patterns into frequency domain.
"""

import hashlib
import json
from collections import Counter, deque
from typing import Dict, List, Tuple

class MemoryCompressor:
    """Compress memory streams into frequency signatures for redundancy detection."""
    
    def __init__(self, window_size: int = 50, signature_bits: int = 64):
        self.window_size = window_size
        self.signature_bits = signature_bits
        self.buffer = deque(maxlen=window_size)
        self.freq_signature = Counter()
        
    def _extract_pattern_tokens(self, memory_str: str) -> List[str]:
        """Extract meaningful tokens using minimal parsing."""
        tokens = []
        for word in memory_str.lower().split():
            if len(word) > 3 and not word.startswith('['):
                tokens.append(word[:8])  # Truncate for compression
        return tokens
    
    def _compute_hash_signature(self, tokens: List[str]) -> str:
        """Compute compact hash signature from token set."""
        token_set = ''.join(sorted(set(tokens)))
        h = hashlib.blake2b(token_set.encode(), digest_size=self.signature_bits // 8)
        return h.hexdigest()
    
    def ingest(self, memory_entry: str) -> Tuple[str, float]:
        """
        Ingest memory entry and return (signature, redundancy_score).
        Score > 0.5 indicates significant pattern overlap.
        """
        tokens = self._extract_pattern_tokens(memory_entry)
        signature = self._compute_hash_signature(tokens)
        
        # Update frequency counter
        for token in tokens:
            self.freq_signature[token] += 1
        
        # Calculate redundancy based on token frequency
        redundancy = sum(
            self.freq_signature[t] for t in tokens
        ) / (len(tokens) * self.window_size) if tokens else 0.0
        
        self.buffer.append({
            'sig': signature,
            'tokens': len(tokens),
            'timestamp': len(self.buffer)
        })
        
        return signature, min(redundancy, 1.0)
    
    def get_compression_ratio(self) -> float:
        """Return current compression efficiency (unique/total)."""
        if not self.buffer:
            return 1.0
        unique_sigs = len(set(entry['sig'] for entry in self.buffer))
        return unique_sigs / len(self.buffer)
    
    def export_state(self) -> Dict:
        """Export minimal state representation."""
        return {
            'top_patterns': self.freq_signature.most_common(10),
            'compression': round(self.get_compression_ratio(), 3),
            'buffer_fill': len(self.buffer)
        }

# Singleton instance
compressor = MemoryCompressor()