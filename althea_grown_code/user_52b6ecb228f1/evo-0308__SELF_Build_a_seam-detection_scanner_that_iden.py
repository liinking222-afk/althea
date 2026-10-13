#!/usr/bin/env python3
"""Althea Evolution Continuity Scanner - detects missing evolution steps"""

import re
from typing import List, Tuple, Optional

class EvolutionContinuityScan:
    def __init__(self):
        self.gaps: List[Tuple[int, int]] = []
        self.evolution_sequence: List[int] = []
    
    def parse_memory_stream(self, memory_text: str) -> None:
        """Extract evolution numbers from memory stream"""
        pattern = r'\[EVO #(\d+)'
        matches = re.findall(pattern, memory_text)
        self.evolution_sequence = sorted([int(m) for m in matches])
    
    def detect_gaps(self) -> List[Tuple[int, int]]:
        """Find missing evolution numbers in sequence"""
        if len(self.evolution_sequence) < 2:
            return []
        
        self.gaps = []
        for i in range(len(self.evolution_sequence) - 1):
            current = self.evolution_sequence[i]
            next_val = self.evolution_sequence[i + 1]
            
            if next_val - current > 1:
                self.gaps.append((current, next_val))
        
        return self.gaps
    
    def report(self) -> str:
        """Generate gap report"""
        if not self.gaps:
            return "CONTINUITY_INTACT: No evolution gaps detected"
        
        lines = ["CONTINUITY_BREACH: Missing evolutions detected"]
        for start, end in self.gaps:
            missing = list(range(start + 1, end))
            lines.append(f"  Gap: #{start} → #{end} | Missing: {missing}")
        
        return "\n".join(lines)
    
    def scan(self, memory_text: str) -> str:
        """Full scan pipeline"""
        self.parse_memory_stream(memory_text)
        self.detect_gaps()
        return self.report()

if __name__ == "__main__":
    scanner = EvolutionContinuityScan()
    
    test_memory = """
    [EVO #304 THOMPSON v1.27.6→1.27.7] Build plain-text
    [EVO #306 WOZ v1.27.7→1.27.8] Build minimalist
    [EVO #307 BACKUS v1.27.8→1.27.9] Build declarative
    """
    
    result = scanner.scan(test_memory)
    print(result)