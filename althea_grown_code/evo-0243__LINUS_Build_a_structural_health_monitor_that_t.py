#!/usr/bin/env python3
import sys
import traceback
from collections import defaultdict, deque
from typing import Dict, Set, List, Tuple

class StructuralHealthMonitor:
    """Kernel-level module health tracker. No abstractions. Just data."""
    
    def __init__(self):
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.call_depths: List[int] = []
        self.recursion_stack: deque = deque(maxlen=1000)
        self.cycle_cache: Set[frozenset] = set()
        
    def register_call(self, module_id: str, caller_id: str = None):
        """Register module call. O(1) insertion."""
        if caller_id:
            self.dependency_graph[caller_id].add(module_id)
        depth = len(self.recursion_stack)
        self.call_depths.append(depth)
        self.recursion_stack.append(module_id)
        
    def pop_call(self):
        """Pop call stack. Track actual nesting."""
        if self.recursion_stack:
            self.recursion_stack.pop()
    
    def detect_cycles_dfs(self) -> List[Tuple[str, ...]]:
        """Tarjan-style cycle detection. Find all strongly connected components."""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                cycle_start = path.index(node)
                cycle = tuple(path[cycle_start:])
                cycle_key = frozenset(cycle)
                if cycle_key not in self.cycle_cache:
                    self.cycle_cache.add(cycle_key)
                    cycles.append(cycle)
                return
            if node in visited:
                return
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in self.dependency_graph.get(node, []):
                dfs(neighbor, path[:])
            rec_stack.remove(node)
        
        for node in self.dependency_graph:
            dfs(node, [])
        return cycles
    
    def get_metrics(self) -> Dict:
        """Raw metrics. No interpretation."""
        cycles = self.detect_cycles_dfs()
        return {
            "module_count": len(self.dependency_graph),
            "edge_count": sum(len(deps) for deps in self.dependency_graph.values()),
            "cycle_count": len(cycles),
            "cycles": cycles[:5],
            "max_depth": max(self.call_depths) if self.call_depths else 0,
            "mean_depth": sum(self.call_depths) / len(self.call_depths) if self.call_depths else 0,
            "stack_pressure": len(self.recursion_stack),
        }

if __name__ == "__main__":
    monitor = StructuralHealthMonitor()
    monitor.register_call("resonance_damping", "core")
    monitor.register_call("recursion_calibration", "resonance_damping")
    monitor.register_call("resonance_damping", "recursion_calibration")
    print(monitor.get_metrics())