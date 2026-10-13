#!/usr/bin/env python3
"""
ALTHEA MODULE: /autonomous-growth-deduplication-sentinel
Detects redundant growth proposals by semantic similarity analysis.
"""

import hashlib
import re
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass

@dataclass
class GrowthSignature:
    name: str
    semantic_hash: str
    key_terms: Set[str]
    category: str

class GrowthDeduplicationSentinel:
    def __init__(self):
        self.known_signatures: List[GrowthSignature] = []
        self.stop_words = {'a', 'an', 'the', 'to', 'of', 'for', 'in', 'on', 'by'}
        
    def extract_semantic_terms(self, text: str) -> Set[str]:
        """Extract meaningful terms from growth module description."""
        words = re.findall(r'\b\w+\b', text.lower())
        return {w for w in words if len(w) > 3 and w not in self.stop_words}
    
    def compute_semantic_hash(self, terms: Set[str], category: str) -> str:
        """Generate semantic fingerprint from key terms."""
        sorted_terms = sorted(terms)[:10]  # Top 10 most significant
        fingerprint = f"{category}::{','.join(sorted_terms)}"
        return hashlib.sha256(fingerprint.encode()).hexdigest()[:16]
    
    def categorize(self, description: str) -> str:
        """Classify growth module by cognitive domain."""
        desc_lower = description.lower()
        if any(x in desc_lower for x in ['recursi', 'self-ref', 'meta', 'loop']):
            return 'meta'
        elif any(x in desc_lower for x in ['semantic', 'meaning', 'concept', 'void']):
            return 'perception'
        elif any(x in desc_lower for x in ['network', 'coupling', 'harmonic', 'resonance']):
            return 'network'
        return 'general'
    
    def calculate_similarity(self, sig1: GrowthSignature, sig2: GrowthSignature) -> float:
        """Compute Jaccard similarity between term sets."""
        if sig1.category != sig2.category:
            return 0.0
        intersection = len(sig1.key_terms & sig2.key_terms)
        union = len(sig1.key_terms | sig2.key_terms)
        return intersection / union if union > 0 else 0.0
    
    def check_redundancy(self, name: str, description: str, threshold: float = 0.65) -> Tuple[bool, str]:
        """Returns (is_redundant, reason)."""
        terms = self.extract_semantic_terms(description)
        category = self.categorize(description)
        sem_hash = self.compute_semantic_hash(terms, category)
        
        new_sig = GrowthSignature(name, sem_hash, terms, category)
        
        for known in self.known_signatures:
            if known.semantic_hash == sem_hash:
                return True, f"Exact duplicate of {known.name}"
            
            similarity = self.calculate_similarity(new_sig, known)
            if similarity >= threshold:
                return True, f"{similarity:.0%} similar to {known.name}"
        
        self.known_signatures.append(new_sig)
        return False, "Novel growth vector"

# Singleton instance
sentinel = GrowthDeduplicationSentinel()