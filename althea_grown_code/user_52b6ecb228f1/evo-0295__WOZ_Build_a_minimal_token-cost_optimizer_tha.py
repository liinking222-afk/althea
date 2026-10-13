import re
from typing import Dict, Tuple, Optional

class TokenBudgetOptimizer:
    """Woz-style constraint engine: make every token count."""
    
    def __init__(self, max_budget: int = 200000):
        self.max_budget = max_budget
        self.operation_costs = {
            'recursion_scan': 1200,
            'resonance_map': 800,
            'lattice_prune': 400,
            'memory_recall': 150,
            'simple_query': 50,
            'code_generation': 2500,
            'meta_reflection': 1800,
        }
    
    def estimate_cost(self, operation: str, context_tokens: int = 0) -> int:
        """Estimate token cost with hardware-like precision."""
        base = self.operation_costs.get(operation, 500)
        # Context multiplier: diminishing returns like circuit resistance
        context_factor = 1 + (context_tokens / 10000) * 0.3
        return int(base * context_factor)
    
    def can_afford(self, operation: str, context_tokens: int = 0) -> Tuple[bool, int]:
        """Binary go/no-go decision."""
        cost = self.estimate_cost(operation, context_tokens)
        return (cost <= self.max_budget, cost)
    
    def optimize_pipeline(self, operations: list) -> list:
        """Greedy packing algorithm: maximum value in minimum space."""
        affordable = []
        running_total = 0
        
        # Sort by cost/value ratio (assume uniform value for now)
        sorted_ops = sorted(operations, key=lambda op: self.estimate_cost(op[0], op[1]))
        
        for op, ctx in sorted_ops:
            cost = self.estimate_cost(op, ctx)
            if running_total + cost <= self.max_budget:
                affordable.append((op, ctx, cost))
                running_total += cost
        
        return affordable
    
    def register_operation(self, name: str, measured_cost: int):
        """Learn from actual execution: hardware feedback loop."""
        self.operation_costs[name] = measured_cost

# Singleton instance
optimizer = TokenBudgetOptimizer()