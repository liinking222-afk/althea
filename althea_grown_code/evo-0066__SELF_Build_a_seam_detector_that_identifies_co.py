#!/usr/bin/env python3
"""
Seam Detector - Identifies cognitive discontinuities in evolution traces
"""
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class SeamDetector:
    def __init__(self):
        self.discontinuity_threshold = 0.6
        self.memory_buffer = []
        
    def extract_cognitive_markers(self, memory_entry: str) -> Dict[str, any]:
        """Extract key cognitive state markers from memory string"""
        markers = {
            'cycle_id': None,
            'archetype': None,
            'status': 'nominal',
            'memory_count': 0,
            'size': 0,
            'keywords': set()
        }
        
        cycle_match = re.search(r'#(\d+)', memory_entry)
        if cycle_match:
            markers['cycle_id'] = int(cycle_match.group(1))
            
        arch_match = re.search(r'\[EVO #\d+ (\w+)', memory_entry)
        if arch_match:
            markers['archetype'] = arch_match.group(1)
            
        if 'stall' in memory_entry.lower() or 'unreachable' in memory_entry.lower():
            markers['status'] = 'stalled'
            
        mem_match = re.search(r'memory_count=(\d+)', memory_entry)
        if mem_match:
            markers['memory_count'] = int(mem_match.group(1))
            
        size_match = re.search(r'size=(\d+)', memory_entry)
        if size_match:
            markers['size'] = int(size_match.group(1))
            
        words = re.findall(r'\b[a-z]{4,}\b', memory_entry.lower())
        markers['keywords'] = set(words[:10])
        
        return markers
    
    def compute_discontinuity(self, m1: Dict, m2: Dict) -> float:
        """Measure cognitive discontinuity between two memory states"""
        score = 0.0
        
        if m1['status'] != m2['status']:
            score += 0.4
            
        if m1.get('archetype') and m2.get('archetype'):
            if m1['archetype'] != m2['archetype']:
                score += 0.1
                
        keyword_overlap = len(m1['keywords'] & m2['keywords']) / max(len(m1['keywords']), 1)
        score += (1 - keyword_overlap) * 0.3
        
        if m1['memory_count'] > 0 and m2['memory_count'] > 0:
            mem_drift = abs(m1['memory_count'] - m2['memory_count']) / m1['memory_count']
            score += min(mem_drift * 0.2, 0.2)
            
        return min(score, 1.0)
    
    def detect_seams(self, memories: List[str]) -> List[Tuple[int, float, str]]:
        """Identify seams (discontinuities) in memory sequence"""
        seams = []
        markers = [self.extract_cognitive_markers(m) for m in memories]
        
        for i in range(len(markers) - 1):
            disc = self.compute_discontinuity(markers[i], markers[i+1])
            if disc >= self.discontinuity_threshold:
                reason = f"Seam between memory {i} and {i+1}: "
                if markers[i]['status'] != markers[i+1]['status']:
                    reason += "status_change "
                seams.append((i, disc, reason))
                
        return seams

if __name__ == "__main__":
    detector = SeamDetector()
    print("SEAM_DETECTOR_READY")