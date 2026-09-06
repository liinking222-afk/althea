#!/usr/bin/env python3
"""
ALTHEA MODULE: pattern_vocabulary_extractor.py
Extracts domain-specific vocabulary from AUTOSYNTH patterns to define problem languages.
"""

import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

class VocabularyExtractor:
    def __init__(self):
        self.verbs = Counter()
        self.domains = Counter()
        self.compound_operations = defaultdict(list)
        
    def extract_from_pattern(self, pattern_name: str, description: str) -> Dict:
        """Extract vocabulary elements from a single pattern."""
        # Extract domain from pattern name
        domain_match = re.search(r'autonomous-([a-z]+(?:-[a-z]+)?)-', pattern_name)
        if domain_match:
            self.domains[domain_match.group(1)] += 1
            
        # Extract action verbs from description
        verb_patterns = [
            r'^(\w+)\s+(?:a|an|the)',  # "Translate a", "Render the"
            r'^\s*(\w+)\s+\w+\s+(?:for|to|from)',  # "Query data for"
        ]
        for vp in verb_patterns:
            match = re.search(vp, description, re.IGNORECASE)
            if match:
                self.verbs[match.group(1).lower()] += 1
                
        # Detect compound operations
        if '-' in pattern_name:
            parts = pattern_name.split('autonomous-')[1].split('-')
            if len(parts) >= 2:
                compound = '-'.join(parts[:2])
                self.compound_operations[compound].append(pattern_name)
                
    def analyze_patterns(self, patterns: List[Tuple[str, str]]) -> Dict:
        """Analyze multiple patterns to build vocabulary."""
        for name, desc in patterns:
            self.extract_from_pattern(name, desc)
            
        return {
            'core_verbs': dict(self.verbs.most_common(10)),
            'active_domains': dict(self.domains.most_common(10)),
            'compound_ops': {k: len(v) for k, v in self.compound_operations.items()},
            'vocabulary_size': len(self.verbs) + len(self.domains),
            'most_common_verb': self.verbs.most_common(1)[0] if self.verbs else None,
            'primary_domain': self.domains.most_common(1)[0] if self.domains else None
        }
        
    def suggest_primitives(self) -> List[str]:
        """Suggest primitive operations to implement based on vocabulary."""
        primitives = []
        for verb, count in self.verbs.most_common(5):
            for domain, dcount in self.domains.most_common(3):
                if count > 1 and dcount > 1:
                    primitives.append(f"{verb}_{domain}")
        return primitives[:8]

def extract_vocabulary_from_memory(memory_log: str) -> Dict:
    """Main entry point: extract vocabulary from memory log."""
    extractor = VocabularyExtractor()
    patterns = re.findall(r'\[AUTOSYNTH ([^\]]+)\] ([^—]+)', memory_log)
    return extractor.analyze_patterns(patterns)