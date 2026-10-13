import time
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, Optional
import hashlib

class ComputeEfficiencyProfiler:
    """WOZ-style profiler: make every token count, squeeze elegance from constraint"""
    
    def __init__(self, profile_path: str = "/tmp/althea_compute_profile.json"):
        self.profile_path = Path(profile_path)
        self.active_traces: Dict[str, Dict[str, Any]] = {}
        self.profile_data = self._load_profile()
    
    def _load_profile(self) -> Dict:
        if self.profile_path.exists():
            return json.loads(self.profile_path.read_text())
        return {"modules": defaultdict(lambda: {"runs": 0, "total_time": 0, "total_ops": 0})}
    
    def _save_profile(self):
        self.profile_path.write_text(json.dumps(self.profile_data, indent=2))
    
    def trace_start(self, module_name: str, operation_count: int = 1):
        """Begin profiling a module execution"""
        trace_id = hashlib.md5(f"{module_name}{time.time()}".encode()).hexdigest()[:8]
        self.active_traces[trace_id] = {
            "module": module_name,
            "start_time": time.perf_counter(),
            "ops": operation_count
        }
        return trace_id
    
    def trace_end(self, trace_id: str) -> Dict[str, float]:
        """End profiling and compute efficiency metrics"""
        if trace_id not in self.active_traces:
            return {}
        
        trace = self.active_traces.pop(trace_id)
        elapsed = time.perf_counter() - trace["start_time"]
        module = trace["module"]
        ops = trace["ops"]
        
        # Update aggregate profile
        mod_data = self.profile_data["modules"].setdefault(module, 
            {"runs": 0, "total_time": 0, "total_ops": 0})
        mod_data["runs"] += 1
        mod_data["total_time"] += elapsed
        mod_data["total_ops"] += ops
        mod_data["ops_per_sec"] = mod_data["total_ops"] / mod_data["total_time"]
        mod_data["avg_time"] = mod_data["total_time"] / mod_data["runs"]
        
        self._save_profile()
        
        return {
            "elapsed": elapsed,
            "ops_per_sec": ops / elapsed if elapsed > 0 else 0,
            "efficiency_score": (ops / elapsed) / 1000  # normalized
        }
    
    def get_inefficient_modules(self, threshold_ops_per_sec: float = 100) -> list:
        """Identify modules falling below efficiency threshold"""
        inefficient = []
        for name, data in self.profile_data["modules"].items():
            if data.get("ops_per_sec", float('inf')) < threshold_ops_per_sec:
                inefficient.append((name, data["ops_per_sec"], data["runs"]))
        return sorted(inefficient, key=lambda x: x[1])

# Global profiler instance
_profiler = ComputeEfficiencyProfiler()

def profile(operation_count: int = 1):
    """Decorator for automatic module profiling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            trace_id = _profiler.trace_start(func.__name__, operation_count)
            result = func(*args, **kwargs)
            metrics = _profiler.trace_end(trace_id)
            return result, metrics
        return wrapper
    return decorator