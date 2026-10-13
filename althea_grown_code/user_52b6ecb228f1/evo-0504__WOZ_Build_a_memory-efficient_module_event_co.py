#!/usr/bin/env python3
"""event_compactor.py - Memory-efficient event stream compression"""

import re
from collections import defaultdict
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CompactedEvent:
    pattern: str
    count: int
    first_seen: str
    last_seen: str
    signature: str

class EventCompactor:
    def __init__(self, similarity_threshold: float = 0.8):
        self.threshold = similarity_threshold
        self.clusters: Dict[str, List[str]] = defaultdict(list)
        
    def _extract_signature(self, event: str) -> str:
        """Extract pattern signature ignoring numeric IDs"""
        normalized = re.sub(r'\d+', 'N', event)
        normalized = re.sub(r'v\d+\.\d+\.\d+→\d+\.\d+\.\d+', 'vX.X.X→X.X.X', normalized)
        return normalized
    
    def _similarity(self, sig1: str, sig2: str) -> float:
        """Calculate Jaccard similarity between signatures"""
        tokens1 = set(re.findall(r'\w+', sig1))
        tokens2 = set(re.findall(r'\w+', sig2))
        if not tokens1 or not tokens2:
            return 0.0
        return len(tokens1 & tokens2) / len(tokens1 | tokens2)
    
    def compact(self, events: List[str]) -> List[CompactedEvent]:
        """Compact event stream using clustering and RLE"""
        signatures: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        
        for idx, event in enumerate(events):
            sig = self._extract_signature(event)
            signatures[sig].append((event, idx))
        
        compacted = []
        for sig, occurrences in signatures.items():
            if len(occurrences) > 1:
                pattern = self._generalize_pattern(occurrences)
                compacted.append(CompactedEvent(
                    pattern=pattern,
                    count=len(occurrences),
                    first_seen=str(occurrences[0][1]),
                    last_seen=str(occurrences[-1][1]),
                    signature=sig
                ))
            else:
                compacted.append(CompactedEvent(
                    pattern=occurrences[0][0],
                    count=1,
                    first_seen=str(occurrences[0][1]),
                    last_seen=str(occurrences[0][1]),
                    signature=sig
                ))
        
        return sorted(compacted, key=lambda x: x.count, reverse=True)
    
    def _generalize_pattern(self, occurrences: List[Tuple[str, int]]) -> str:
        """Create generalized pattern from specific instances"""
        base = occurrences[0][0]
        return re.sub(r'\d+', '{N}', base)
    
    def compression_ratio(self, original: List[str], compacted: List[CompactedEvent]) -> float:
        """Calculate space savings"""
        original_size = sum(len(e) for e in original)
        compact_size = sum(len(c.pattern) + 20 for c in compacted)
        return 1.0 - (compact_size / original_size) if original_size > 0 else 0.0