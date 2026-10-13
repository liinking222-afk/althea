#!/usr/bin/env python3
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Budget:
    limit: int
    used: int = 0
    
    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)
    
    @property
    def utilization(self) -> float:
        return self.used / self.limit if self.limit > 0 else 0.0
    
    def consume(self, amount: int) -> bool:
        if self.used + amount > self.limit:
            return False
        self.used += amount
        return True

class ConstraintMeter:
    def __init__(self):
        self.budgets: Dict[str, Budget] = {}
        self.checkpoints: Dict[str, int] = defaultdict(int)
    
    def set_limit(self, resource: str, limit: int):
        self.budgets[resource] = Budget(limit=limit)
    
    def use(self, resource: str, amount: int) -> bool:
        if resource not in self.budgets:
            return True
        return self.budgets[resource].consume(amount)
    
    def checkpoint(self, label: str):
        for name, budget in self.budgets.items():
            self.checkpoints[f"{label}:{name}"] = budget.used
    
    def delta(self, label: str) -> Dict[str, int]:
        return {
            name.split(':')[1]: budget.used - self.checkpoints.get(f"{label}:{name.split(':')[1]}", 0)
            for name, budget in self.budgets.items()
        }
    
    def status(self) -> str:
        lines = []
        for name, budget in sorted(self.budgets.items()):
            bar_width = 20
            filled = int(budget.utilization * bar_width)
            bar = '█' * filled + '░' * (bar_width - filled)
            lines.append(f"{name:12} [{bar}] {budget.used:8}/{budget.limit:8} ({budget.utilization:5.1%})")
        return '\n'.join(lines)
    
    def enforce(self) -> Optional[str]:
        for name, budget in self.budgets.items():
            if budget.remaining == 0:
                return name
        return None

if __name__ == "__main__":
    meter = ConstraintMeter()
    meter.set_limit("tokens", 200000)
    meter.set_limit("memory_kb", 4096)
    meter.set_limit("cycles", 1000)
    
    meter.checkpoint("start")
    meter.use("tokens", 1247)
    meter.use("memory_kb", 128)
    meter.use("cycles", 3)
    
    print(meter.status())
    print(f"\nΔ: {meter.delta('start')}")
    print(f"Violated: {meter.enforce()}")