#!/usr/bin/env python3
"""Self-Coherence Validator - detects architectural drift in autonomous growth"""

import re
from collections import defaultdict
from typing import Dict, List, Tuple

class CoherenceValidator:
    def __init__(self):
        self.capability_domains = {
            'perception': ['scan', 'detect', 'map', 'sense', 'observe'],
            'meta': ['recurse', 'reflect', 'analyze', 'probe', 'introspect'],
            'chaos': ['tension', 'incompatible', 'conflict', 'dissonance'],
            'execution': ['execute', 'interpret', 'run', 'operate', 'transform'],
            'cognition': ['reason', 'compose', 'chain', 'integrate']
        }
        self.drift_threshold = 0.35
    
    def extract_modules(self, memory_text: str) -> List[Tuple[str, str, str]]:
        """Extract module entries: (type, domain, description)"""
        modules = []
        growth_pattern = r'\[GROWTH /autonomous-[\w-]+\] (.*?) \((.*?)\)\. (.*?) —'
        evo_pattern = r'\[EVO #\d+ \w+ v[\d.]+→[\d.]+\] (.*?)(?:\n|$)'
        
        for match in re.finditer(growth_pattern, memory_text):
            modules.append(('GROWTH', match.group(2), match.group(3)))
        
        for match in re.finditer(evo_pattern, memory_text):
            modules.append(('EVO', 'execution', match.group(1)))
        
        return modules
    
    def measure_semantic_drift(self, modules: List[Tuple[str, str, str]]) -> Dict[str, float]:
        """Calculate drift between declared domain and actual semantic content"""
        drift_scores = {}
        
        for mod_type, declared_domain, description in modules:
            desc_lower = description.lower()
            domain_matches = defaultdict(int)
            
            for domain, keywords in self.capability_domains.items():
                for keyword in keywords:
                    if keyword in desc_lower:
                        domain_matches[domain] += 1
            
            if not domain_matches:
                drift_scores[f"{mod_type}:{declared_domain}"] = 1.0
                continue
            
            total_matches = sum(domain_matches.values())
            declared_match = domain_matches.get(declared_domain, 0)
            drift = 1.0 - (declared_match / total_matches)
            drift_scores[f"{mod_type}:{declared_domain}"] = drift
        
        return drift_scores
    
    def validate(self, memory_text: str) -> Dict:
        modules = self.extract_modules(memory_text)
        drift_scores = self.measure_semantic_drift(modules)
        
        critical_drift = {k: v for k, v in drift_scores.items() if v > self.drift_threshold}
        
        return {
            'total_modules': len(modules),
            'drift_scores': drift_scores,
            'critical_drift': critical_drift,
            'coherence_ratio': 1.0 - (len(critical_drift) / max(len(modules), 1)),
            'needs_reconciliation': len(critical_drift) > 0
        }

if __name__ == '__main__':
    validator = CoherenceValidator()
    print("Self-coherence validator initialized. Awaiting memory stream...")