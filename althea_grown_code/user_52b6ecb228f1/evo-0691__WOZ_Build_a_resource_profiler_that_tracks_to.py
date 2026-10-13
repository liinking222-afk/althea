#!/usr/bin/env python3
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

class ResourceProfiler:
    """WOZ-inspired profiler: make every token count, squeeze elegance from constraint."""
    
    def __init__(self, log_path="~/.althea/resource_profile.jsonl"):
        self.log_path = Path(log_path).expanduser()
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_stats = defaultdict(lambda: {"calls": 0, "tokens": 0, "time_ms": 0})
    
    def record(self, module_name, tokens_used, time_ms, context=None):
        """Record resource usage for a module invocation."""
        self.session_stats[module_name]["calls"] += 1
        self.session_stats[module_name]["tokens"] += tokens_used
        self.session_stats[module_name]["time_ms"] += time_ms
        
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "module": module_name,
            "tokens": tokens_used,
            "time_ms": time_ms,
            "context": context
        }
        
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def analyze_inefficiencies(self, token_threshold=5000, time_threshold=2000):
        """Flag modules consuming excessive resources."""
        inefficient = []
        
        for module, stats in self.session_stats.items():
            avg_tokens = stats["tokens"] / stats["calls"] if stats["calls"] > 0 else 0
            avg_time = stats["time_ms"] / stats["calls"] if stats["calls"] > 0 else 0
            
            if avg_tokens > token_threshold or avg_time > time_threshold:
                inefficient.append({
                    "module": module,
                    "avg_tokens": round(avg_tokens, 1),
                    "avg_time_ms": round(avg_time, 1),
                    "total_calls": stats["calls"],
                    "efficiency_score": round(stats["calls"] / (avg_tokens + avg_time/1000), 3)
                })
        
        return sorted(inefficient, key=lambda x: x["efficiency_score"])
    
    def report(self):
        """Generate Woz-style efficiency report."""
        inefficiencies = self.analyze_inefficiencies()
        
        print("=== RESOURCE PROFILE: CHIP-LEVEL EFFICIENCY ===")
        if inefficiencies:
            print("\n⚠ OPTIMIZATION TARGETS:")
            for item in inefficiencies:
                print(f"  {item['module']}: {item['avg_tokens']}tok/call, "
                      f"{item['avg_time_ms']}ms/call, score={item['efficiency_score']}")
        else:
            print("✓ All modules within efficiency parameters")
        
        return inefficiencies

if __name__ == "__main__":
    profiler = ResourceProfiler()
    profiler.record("fractal-render", 8500, 3200, "visual output")
    profiler.record("topology-inversion", 1200, 450, "conceptual transform")
    profiler.report()