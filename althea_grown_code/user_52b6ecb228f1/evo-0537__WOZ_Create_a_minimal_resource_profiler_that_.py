#!/usr/bin/env python3
import json
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

class CapabilityDensityProfiler:
    """Woz-style efficiency tracker: capability per token spent."""
    
    def __init__(self, log_path: str = "/tmp/althea_density.jsonl"):
        self.log_path = Path(log_path)
        self.metrics: Dict[str, Dict] = defaultdict(lambda: {
            "invocations": 0,
            "tokens_spent": 0,
            "outcomes_delivered": 0,
            "last_used": 0
        })
    
    def record(self, module: str, tokens: int, outcome_quality: float = 1.0):
        """Log module usage with token cost and outcome quality (0-1)."""
        m = self.metrics[module]
        m["invocations"] += 1
        m["tokens_spent"] += tokens
        m["outcomes_delivered"] += outcome_quality
        m["last_used"] = time.time()
        
        with open(self.log_path, "a") as f:
            f.write(json.dumps({
                "ts": time.time(),
                "module": module,
                "tokens": tokens,
                "quality": outcome_quality
            }) + "\n")
    
    def density_report(self, top_n: int = 10) -> List[tuple]:
        """Return modules ranked by outcome-per-token density."""
        ranked = []
        for mod, m in self.metrics.items():
            if m["tokens_spent"] > 0:
                density = m["outcomes_delivered"] / m["tokens_spent"]
                ranked.append((mod, density, m["invocations"], m["tokens_spent"]))
        
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:top_n]
    
    def suggest_pruning(self, threshold: float = 0.0001) -> List[str]:
        """Identify low-density modules that waste tokens."""
        candidates = []
        for mod, m in self.metrics.items():
            if m["tokens_spent"] > 1000:
                density = m["outcomes_delivered"] / m["tokens_spent"]
                if density < threshold:
                    candidates.append(mod)
        return candidates

if __name__ == "__main__":
    profiler = CapabilityDensityProfiler()
    profiler.record("orbital-prop", 450, 0.95)
    profiler.record("fractal-render", 1200, 0.4)
    profiler.record("salience-inversion", 300, 0.9)
    profiler.record("fractal-render", 1100, 0.3)
    
    print("TOP DENSITY MODULES:")
    for mod, dens, inv, tok in profiler.density_report():
        print(f"  {mod:30s} {dens:.6f} out/tok ({inv} calls, {tok} tokens)")
    
    print("\nPRUNING CANDIDATES:")
    for mod in profiler.suggest_pruning(0.0005):
        print(f"  - {mod}")