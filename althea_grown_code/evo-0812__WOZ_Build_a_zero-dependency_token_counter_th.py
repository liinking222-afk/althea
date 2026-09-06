#!/usr/bin/env python3
"""CHIP: Computational Heuristic for Inference Profiling
Woz-style: count every byte, measure every cycle, no bloat."""

import sys
import time
from typing import Dict, Optional

class CHIP:
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.timers: Dict[str, float] = {}
        self.baseline = len(sys.modules)
    
    def count(self, text: str, label: str = "default") -> int:
        """Count tokens using byte-approximation: ~4 chars per token."""
        tokens = max(1, len(text.encode('utf-8')) // 4)
        self.counters[label] = self.counters.get(label, 0) + tokens
        return tokens
    
    def start(self, label: str = "default") -> None:
        """Start timing a computational block."""
        self.timers[label] = time.perf_counter()
    
    def stop(self, label: str = "default") -> Optional[float]:
        """Stop timing and return elapsed milliseconds."""
        if label not in self.timers:
            return None
        elapsed = (time.perf_counter() - self.timers[label]) * 1000
        del self.timers[label]
        return elapsed
    
    def budget_check(self, label: str, limit: int) -> bool:
        """Check if label is under token budget."""
        return self.counters.get(label, 0) <= limit
    
    def report(self) -> str:
        """Generate minimal resource report."""
        lines = [f"CHIP | {self.baseline} modules"]
        for label, count in sorted(self.counters.items()):
            lines.append(f"  {label}: {count}t")
        return "\n".join(lines)
    
    def reset(self, label: Optional[str] = None) -> None:
        """Reset specific counter or all counters."""
        if label:
            self.counters.pop(label, None)
            self.timers.pop(label, None)
        else:
            self.counters.clear()
            self.timers.clear()

# Singleton instance
chip = CHIP()

if __name__ == "__main__":
    # Self-test
    chip.count("Hello world", "test")
    chip.start("compute")
    time.sleep(0.001)
    elapsed = chip.stop("compute")
    print(chip.report())
    print(f"Compute: {elapsed:.2f}ms")
    print(f"Under 100t budget: {chip.budget_check('test', 100)}")