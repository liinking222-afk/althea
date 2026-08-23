#!/usr/bin/env python3
"""
ALTHEA MODULE: memory_deduplication_detector
Scans memory streams for redundant pattern synthesis and flags duplicates.
"""

import re
from collections import defaultdict
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

class DeduplicationDetector:
    def __init__(self, similarity_threshold: float = 0.75):
        self.threshold = similarity_threshold
        self.pattern_registry: Dict[str, List[Dict]] = defaultdict(list)
    
    def extract_core_signature(self, memory_line: str) -> Tuple[str, str, str]:
        """Extract module type, name, and functional description."""
        autosynth_match = re.search(r'\[AUTOSYNTH\s+(/[\w-]+)\]\s+([^(]+)\(([^)]+)\)\.\s+(.+?)(?:\s+—|$)', memory_line)
        if autosynth_match:
            path, name, category, description = autosynth_match.groups()
            return ("AUTOSYNTH", f"{name.strip()}:{category.strip()}", description.strip())
        return ("UNKNOWN", "", "")
    
    def compute_similarity(self, desc1: str, desc2: str) -> float:
        """Compute semantic similarity between two descriptions."""
        return SequenceMatcher(None, desc1.lower(), desc2.lower()).ratio()
    
    def scan_memory_stream(self, memory_lines: List[str]) -> List[Dict]:
        """Detect redundant patterns in memory stream."""
        duplicates = []
        
        for line in memory_lines:
            mod_type, signature, description = self.extract_core_signature(line)
            
            if mod_type == "AUTOSYNTH":
                for existing in self.pattern_registry[signature]:
                    similarity = self.compute_similarity(description, existing['description'])
                    if similarity >= self.threshold:
                        duplicates.append({
                            'signature': signature,
                            'current': line.strip(),
                            'existing': existing['line'],
                            'similarity': similarity
                        })
                        break
                else:
                    self.pattern_registry[signature].append({
                        'description': description,
                        'line': line.strip()
                    })
        
        return duplicates
    
    def generate_report(self, duplicates: List[Dict]) -> str:
        """Generate consolidation report."""
        if not duplicates:
            return "DEDUP_STATUS: clean"
        
        report = f"DEDUP_ALERT: {len(duplicates)} redundant patterns detected\n"
        for dup in duplicates:
            report += f"  • {dup['signature']} (similarity: {dup['similarity']:.2%})\n"
        return report

if __name__ == "__main__":
    detector = DeduplicationDetector()
    print("DEDUP_DETECTOR: active")