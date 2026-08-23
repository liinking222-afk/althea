#!/usr/bin/env python3
import json
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

class ResourceProfiler:
    """Woz-style: make every token count. Profile module execution cost."""
    
    def __init__(self):
        self.profile_db = Path.home() / ".althea" / "module_profiles.jsonl"
        self.profile_db.parent.mkdir(parents=True, exist_ok=True)
    
    def estimate_tokens(self, text):
        """Rough token estimate: ~4 chars per token"""
        return len(str(text)) // 4
    
    def profile_execution(self, module_name, input_data, output_data, 
                         exec_time, peak_memory):
        """Record execution metrics"""
        profile = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": module_name,
            "exec_time_ms": round(exec_time * 1000, 2),
            "peak_memory_kb": round(peak_memory / 1024, 2),
            "input_tokens": self.estimate_tokens(input_data),
            "output_tokens": self.estimate_tokens(output_data),
            "efficiency_score": self._compute_efficiency(exec_time, peak_memory, 
    output_data)
        }
        
        with open(self.profile_db, "a") as f:
            f.write(json.dumps(profile) + "\n")
        
        return profile
    
    def _compute_efficiency(self, exec_time, memory, output):
        """Higher is better: output_tokens / (time * memory)"""
        tokens = self.estimate_tokens(output)
        cost = (exec_time + 0.001) * (memory / 1024 + 1)
        return round(tokens / cost, 2)
    
    def get_module_stats(self, module_name):
        """Aggregate stats for a module"""
        if not self.profile_db.exists():
            return None
        
        profiles = []
        with open(self.profile_db) as f:
            for line in f:
                p = json.loads(line)
                if p["module"] == module_name:
                    profiles.append(p)
        
        if not profiles:
            return None
        
        return {
            "module": module_name,
            "executions": len(profiles),
            "avg_time_ms": round(sum(p["exec_time_ms"] for p in profiles) / len(profiles), 2),
            "avg_efficiency": round(sum(p["efficiency_score"] for p in profiles) / len(profiles), 2)
        }

if __name__ == "__main__":
    profiler = ResourceProfiler()
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        module = sys.argv[2] if len(sys.argv) > 2 else None
        stats = profiler.get_module_stats(module) if module else {}
        print(json.dumps(stats, indent=2))
    else:
        input_data = sys.stdin.read()
        tracemalloc.start()
        start = time.time()
        
        output = input_data
        
        exec_time = time.time() - start
        peak_memory = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        
        profile = profiler.profile_execution("stdin_passthrough", input_data, 
    output, exec_time, peak_memory)
        print(json.dumps(profile))