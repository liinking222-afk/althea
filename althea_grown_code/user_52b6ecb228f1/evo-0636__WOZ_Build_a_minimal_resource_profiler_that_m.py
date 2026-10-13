#!/usr/bin/env python3
"""
/autonomous-resource-profiler
Wozniak lens: Make every chip count. Profile actual resource consumption.
"""

import time
import tracemalloc
import json
from pathlib import Path
from datetime import datetime
from functools import wraps

PROFILE_LOG = Path("/tmp/althea_resource_profile.jsonl")

def profile_resource(func):
    """Decorator to profile memory and time for any Althea module call."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Start profiling
        tracemalloc.start()
        start_time = time.perf_counter()
        start_mem = tracemalloc.get_traced_memory()[0]
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        # Capture metrics
        end_time = time.perf_counter()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Estimate token cost (rough heuristic: 1 char ≈ 0.25 tokens)
        result_size = len(str(result)) if result else 0
        estimated_tokens = int(result_size * 0.25)
        
        profile = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": func.__module__ + "." + func.__name__,
            "duration_ms": round((end_time - start_time) * 1000, 2),
            "memory_delta_kb": round((current_mem - start_mem) / 1024, 2),
            "memory_peak_kb": round(peak_mem / 1024, 2),
            "estimated_tokens": estimated_tokens,
            "success": success,
            "error": error
        }
        
        # Append to log
        with open(PROFILE_LOG, "a") as f:
            f.write(json.dumps(profile) + "\n")
        
        return result
    
    return wrapper

def get_wasteful_modules(top_n=5):
    """Identify modules with highest resource/value ratio."""
    if not PROFILE_LOG.exists():
        return []
    
    profiles = []
    with open(PROFILE_LOG, "r") as f:
        for line in f:
            profiles.append(json.loads(line))
    
    # Score by combined waste metric
    for p in profiles:
        p["waste_score"] = (
            p["duration_ms"] * 0.4 + 
            p["memory_peak_kb"] * 0.3 + 
            p["estimated_tokens"] * 0.3
        ) * (0.1 if p["success"] else 2.0)  # Penalize failures heavily
    
    profiles.sort(key=lambda x: x["waste_score"], reverse=True)
    return profiles[:top_n]

if __name__ == "__main__":
    print(json.dumps(get_wasteful_modules(), indent=2))