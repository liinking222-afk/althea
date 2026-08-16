#!/usr/bin/env python3
import time
import functools
import json
from pathlib import Path
from collections import defaultdict
from typing import Callable, Any

class ResourceProfiler:
    def __init__(self, profile_path: str = "/tmp/althea_resource_profile.json"):
        self.profile_path = Path(profile_path)
        self.metrics = defaultdict(lambda: {"calls": 0, "total_time": 0.0, "token_cost": 0})
        self.load_profile()
    
    def load_profile(self):
        if self.profile_path.exists():
            with open(self.profile_path, 'r') as f:
                data = json.load(f)
                self.metrics = defaultdict(lambda: {"calls": 0, "total_time": 0.0, "token_cost": 0}, data)
    
    def save_profile(self):
        with open(self.profile_path, 'w') as f:
            json.dump(dict(self.metrics), f, indent=2)
    
    def profile(self, token_cost: int = 0):
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start = time.perf_counter()
                result = kwargs.get('_result_override', func(*args, **kwargs))
                elapsed = time.perf_counter() - start
                
                key = f"{func.__module__}.{func.__name__}"
                self.metrics[key]["calls"] += 1
                self.metrics[key]["total_time"] += elapsed
                self.metrics[key]["token_cost"] += token_cost
                
                return result
            return wrapper
        return decorator
    
    def get_inefficient_paths(self, time_threshold: float = 1.0, efficiency_ratio: float = 0.001):
        """Return functions with poor time/token efficiency."""
        inefficient = []
        for key, data in self.metrics.items():
            if data["calls"] == 0:
                continue
            avg_time = data["total_time"] / data["calls"]
            if data["token_cost"] > 0:
                efficiency = avg_time / data["token_cost"]
                if efficiency > efficiency_ratio or avg_time > time_threshold:
                    inefficient.append({
                        "path": key,
                        "avg_time": avg_time,
                        "token_cost": data["token_cost"],
                        "calls": data["calls"],
                        "efficiency": efficiency
                    })
        return sorted(inefficient, key=lambda x: x["efficiency"], reverse=True)
    
    def mark_for_pruning(self):
        """Save inefficient paths to pruning manifest."""
        targets = self.get_inefficient_paths()
        prune_path = Path("/tmp/althea_prune_targets.json")
        with open(prune_path, 'w') as f:
            json.dump(targets, f, indent=2)
        self.save_profile()
        return len(targets)

profiler = ResourceProfiler()