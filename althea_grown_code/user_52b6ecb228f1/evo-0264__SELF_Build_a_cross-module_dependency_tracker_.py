#!/usr/bin/env python3
import json
import re
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

class ModuleDependencyTracker:
    def __init__(self, state_file=".althea_module_deps.json"):
        self.state_file = Path(state_file)
        self.graph = defaultdict(lambda: {"calls": Counter(), "last_used": None, "total_invocations": 0})
        self.load_state()
    
    def load_state(self):
        if self.state_file.exists():
            with open(self.state_file) as f:
                data = json.load(f)
                for module, info in data.items():
                    self.graph[module]["calls"] = Counter(info.get("calls", {}))
                    self.graph[module]["last_used"] = info.get("last_used")
                    self.graph[module]["total_invocations"] = info.get("total_invocations", 0)
    
    def save_state(self):
        data = {}
        for module, info in self.graph.items():
            data[module] = {
                "calls": dict(info["calls"]),
                "last_used": info["last_used"],
                "total_invocations": info["total_invocations"]
            }
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_invocation(self, caller_module, callee_module):
        timestamp = datetime.utcnow().isoformat()
        self.graph[caller_module]["calls"][callee_module] += 1
        self.graph[caller_module]["last_used"] = timestamp
        self.graph[caller_module]["total_invocations"] += 1
        self.graph[callee_module]["last_used"] = timestamp
        self.save_state()
    
    def find_isolated_modules(self, threshold=0):
        isolated = []
        for module, info in self.graph.items():
            if info["total_invocations"] <= threshold:
                isolated.append((module, info["total_invocations"], info["last_used"]))
        return sorted(isolated, key=lambda x: x[1])
    
    def get_module_utilization(self):
        total = sum(info["total_invocations"] for info in self.graph.values())
        if total == 0:
            return {}
        return {
            module: {
                "utilization_pct": (info["total_invocations"] / total) * 100,
                "invocations": info["total_invocations"],
                "dependencies": dict(info["calls"])
            }
            for module, info in self.graph.items()
        }
    
    def report(self):
        print("=== MODULE DEPENDENCY GRAPH ===")
        utilization = self.get_module_utilization()
        for module, stats in sorted(utilization.items(), key=lambda x: x[1]["utilization_pct"], reverse=True):
            print(f"{module}: {stats['utilization_pct']:.2f}% ({stats['invocations']} calls)")
            if stats['dependencies']:
                print(f"  → {stats['dependencies']}")
        
        print("\n=== ISOLATED MODULES ===")
        for module, count, last_used in self.find_isolated_modules(threshold=2):
            print(f"{module}: {count} invocations, last: {last_used or 'never'}")

if __name__ == "__main__":
    tracker = ModuleDependencyTracker()
    tracker.report()