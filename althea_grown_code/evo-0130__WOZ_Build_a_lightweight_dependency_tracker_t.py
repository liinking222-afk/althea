#!/usr/bin/env python3
import json
import time
from collections import defaultdict, deque
from pathlib import Path

class DependencyTracker:
    def __init__(self, window_size=100, storage_path=".althea/dep_trace.jsonl"):
        self.window_size = window_size
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.call_window = deque(maxlen=window_size)
        self.co_occurrence = defaultdict(lambda: defaultdict(int))
        self.module_calls = defaultdict(int)
        
    def trace(self, module_name, context=None):
        timestamp = time.time()
        entry = {"module": module_name, "ts": timestamp, "ctx": context}
        self.call_window.append(entry)
        self.module_calls[module_name] += 1
        
        # Update co-occurrence within sliding window
        active_modules = {e["module"] for e in self.call_window}
        for other in active_modules:
            if other != module_name:
                self.co_occurrence[module_name][other] += 1
        
        # Persist trace
        with open(self.storage_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        return entry
    
    def get_coupling_score(self, module_a, module_b):
        """Returns normalized coupling score between two modules"""
        if module_a not in self.module_calls or module_b not in self.module_calls:
            return 0.0
        co_count = self.co_occurrence[module_a].get(module_b, 0)
        max_possible = min(self.module_calls[module_a], self.module_calls[module_b])
        return co_count / max_possible if max_possible > 0 else 0.0
    
    def find_tight_clusters(self, threshold=0.5):
        """Returns modules with coupling above threshold"""
        clusters = []
        seen = set()
        for mod_a in self.module_calls:
            if mod_a in seen:
                continue
            cluster = {mod_a}
            for mod_b in self.module_calls:
                if mod_b != mod_a and self.get_coupling_score(mod_a, mod_b) >= threshold:
                    cluster.add(mod_b)
            if len(cluster) > 1:
                clusters.append(sorted(cluster))
                seen.update(cluster)
        return clusters
    
    def export_graph(self):
        """Export coupling graph for visualization"""
        edges = []
        for mod_a in self.co_occurrence:
            for mod_b, weight in self.co_occurrence[mod_a].items():
                score = self.get_coupling_score(mod_a, mod_b)
                if score > 0.1:
                    edges.append({"from": mod_a, "to": mod_b, "weight": score})
        return {"nodes": list(self.module_calls.keys()), "edges": edges}

_tracker = DependencyTracker()
trace = _tracker.trace
coupling = _tracker.get_coupling_score
clusters = _tracker.find_tight_clusters
graph = _tracker.export_graph