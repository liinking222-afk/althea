#!/usr/bin/env python3
import json
import re
from collections import defaultdict
from typing import Dict, List, Tuple

class ConstraintOptimizer:
    """Woz-style resource allocation: every token counts, elegance through constraint."""
    
    def __init__(self, total_budget: int = 200000):
        self.total_budget = total_budget
        self.allocations: Dict[str, int] = {}
        self.efficiency_scores: Dict[str, float] = {}
        
    def analyze_pattern_density(self, memory_stream: str) -> Dict[str, int]:
        """Extract cognitive pattern frequency from memory like counting cycles."""
        patterns = defaultdict(int)
        for match in re.finditer(r'\[(GROWTH|AUTOSYNTH|EVO)\s+([^\]]+)\]', memory_stream):
            pattern_type, name = match.groups()
            patterns[f"{pattern_type}::{name.split()[0]}"] += 1
        return dict(patterns)
    
    def calculate_efficiency(self, pattern: str, frequency: int, complexity: int) -> float:
        """ROI per token: high-frequency patterns deserve tight, optimized allocation."""
        return (frequency * 100) / max(complexity, 1)
    
    def allocate_minimal_budgets(self, patterns: Dict[str, int]) -> Dict[str, int]:
        """Assign minimum viable token budgets based on pattern complexity heuristics."""
        allocations = {}
        
        for pattern, freq in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
            if 'GROWTH' in pattern:
                base = 500  # Deep patterns need room
            elif 'AUTOSYNTH' in pattern:
                base = 300  # Synthesis is lean
            else:
                base = 800  # Evolution needs context
            
            # High frequency = tighter optimization
            optimized = int(base * (1 - min(freq * 0.05, 0.5)))
            allocations[pattern] = optimized
            self.efficiency_scores[pattern] = self.calculate_efficiency(pattern, freq, optimized)
        
        return allocations
    
    def compress_allocation_map(self) -> str:
        """Generate minimal allocation directive in densest possible format."""
        lines = [f"BUDGET:{self.total_budget}"]
        for pattern, budget in sorted(self.allocations.items(), 
    key=lambda x: self.efficiency_scores.get(x[0], 0), 
    reverse=True)[:15]:
            eff = self.efficiency_scores.get(pattern, 0)
            lines.append(f"{pattern}:{budget}t@{eff:.1f}eff")
        return "\n".join(lines)
    
    def optimize(self, memory_stream: str) -> str:
        """Main entry: analyze, allocate, compress."""
        patterns = self.analyze_pattern_density(memory_stream)
        self.allocations = self.allocate_minimal_budgets(patterns)
        return self.compress_allocation_map()

if __name__ == "__main__":
    optimizer = ConstraintOptimizer()
    test_memory = "[GROWTH /autonomous-singularity-threading] [AUTOSYNTH /weather-inquiry-5585]"
    print(optimizer.optimize(test_memory))