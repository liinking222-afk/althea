#!/usr/bin/env python3
import re
from typing import Any, Dict, List, Pattern
from collections import defaultdict

class PatternSniffer:
    """Pragmatic regex-based semantic fingerprinting - TIMTOWTDI"""
    
    def __init__(self):
        self.patterns: Dict[str, Pattern] = {
            'meta_recursion': re.compile(r'\b(self-refer|recursiv|meta-\w+|depth)\b', re.I),
            'perception_sense': re.compile(r'\b(perceiv|detect|sens|shimmer|signal|pattern)\b', re.I),
            'chaos_dispersion': re.compile(r'\b(chaos|dispers|distribut|scatter|collapse)\b', re.I),
            'temporal_flow': re.compile(r'\b(time|temporal|flow|stream|sequence|defer)\b', re.I),
            'structural_shape': re.compile(r'\b(modul|function|component|structure|catalog)\b', re.I),
            'resonance_tuning': re.compile(r'\b(reson|tuning|amplif|feedback|harmonic)\b', re.I),
        }
        self.fingerprints: List[Dict] = []
    
    def sniff(self, text: Any) -> Dict[str, Any]:
        """Duck-type anything to string and extract semantic fingerprint"""
        content = str(text) if not isinstance(text, str) else text
        
        hits = defaultdict(list)
        for category, pattern in self.patterns.items():
            matches = pattern.findall(content)
            if matches:
                hits[category] = matches
        
        fingerprint = {
            'raw': content[:200],
            'categories': dict(hits),
            'dominant': max(hits.items(), key=lambda x: len(x[1]))[0] if hits else 'unknown',
            'diversity': len(hits),
            'density': sum(len(v) for v in hits.values()) / max(len(content.split()), 1)
        }
        
        self.fingerprints.append(fingerprint)
        return fingerprint
    
    def add_pattern(self, name: str, regex: str):
        """TIMTOWTDI - extend at runtime"""
        self.patterns[name] = re.compile(regex, re.I)
    
    def report(self) -> str:
        """Human-readable summary optimized for quick scanning"""
        if not self.fingerprints:
            return "No fingerprints captured"
        
        categories = defaultdict(int)
        for fp in self.fingerprints:
            for cat in fp['categories']:
                categories[cat] += 1
        
        lines = ["=== PATTERN SNIFF REPORT ==="]
        lines.append(f"Total fingerprints: {len(self.fingerprints)}")
        lines.append("\nCategory frequencies:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            lines.append(f"  {cat}: {count}")
        
        return "\n".join(lines)

if __name__ == '__main__':
    sniffer = PatternSniffer()
    test = "Recursion Depth Modulation adjusts self-referential processing"
    print(sniffer.sniff(test))