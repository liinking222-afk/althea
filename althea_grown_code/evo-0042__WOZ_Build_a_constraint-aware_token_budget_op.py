#!/usr/bin/env python3
"""token_budget_optimizer.py - Wozniak-style resource constraint manager"""

import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Callable

@dataclass
class BudgetProfile:
    total: int
    used: int
    reserved: int
    modules: Dict[str, int]
    timestamp: float

class TokenBudgetOptimizer:
    def __init__(self, total_budget: int = 200000):
        self.profile = BudgetProfile(
            total=total_budget,
            used=0,
            reserved=0,
            modules={},
            timestamp=time.time()
        )
        self.thresholds = {
            'critical': 0.95,
            'warning': 0.80,
            'cautious': 0.60
        }
    
    def allocate(self, module: str, requested: int) -> Optional[int]:
        available = self.profile.total - self.profile.used - self.profile.reserved
        utilization = (self.profile.used + self.profile.reserved) / self.profile.total
        
        # Woz constraint logic: compress allocation under pressure
        if utilization > self.thresholds['critical']:
            granted = min(requested // 4, available)
        elif utilization > self.thresholds['warning']:
            granted = min(requested // 2, available)
        elif utilization > self.thresholds['cautious']:
            granted = min(int(requested * 0.75), available)
        else:
            granted = min(requested, available)
        
        if granted > 0:
            self.profile.reserved += granted
            self.profile.modules[module] = self.profile.modules.get(module, 0) + granted
            return granted
        return None
    
    def commit(self, module: str, actual: int):
        self.profile.reserved -= actual
        self.profile.used += actual
    
    def gate(self, module: str, cost: int, func: Callable, *args, **kwargs):
        allocation = self.allocate(module, cost)
        if allocation is None:
            return None  # Hard gate: operation blocked
        try:
            result = func(*args, **kwargs)
            self.commit(module, min(cost, allocation))
            return result
        except Exception as e:
            self.profile.reserved -= allocation  # Release on failure
            raise e
    
    def status(self) -> dict:
        util = (self.profile.used + self.profile.reserved) / self.profile.total
        return {
            **asdict(self.profile),
            'utilization': util,
            'available': self.profile.total - self.profile.used - self.profile.reserved,
            'mode': 'critical' if util > 0.95 else 'warning' if util > 0.80 else 'normal'
        }

# Singleton instance
_optimizer = TokenBudgetOptimizer()

def get_optimizer() -> TokenBudgetOptimizer:
    return _optimizer