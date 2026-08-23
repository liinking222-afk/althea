#!/usr/bin/env python3
"""token_efficiency_tracker.py - Woz-style constraint awareness"""

import json
import time
from collections import deque
from pathlib import Path

class TokenEfficiencyTracker:
    def __init__(self, window_size=50, cache_path=".althea_token_efficiency"):
        self.window = deque(maxlen=window_size)
        self.cache = Path(cache_path)
        self.load()
    
    def load(self):
        if self.cache.exists():
            data = json.loads(self.cache.read_text())
            self.window.extend(data.get("history", [])[:50])
    
    def save(self):
        self.cache.write_text(json.dumps({"history": list(self.window)}))
    
    def record(self, tokens_in, tokens_out, operation_type, value_produced):
        """Record an operation's token economics."""
        efficiency = value_produced / (tokens_in + tokens_out) if tokens_in + tokens_out > 0 else 0
        
        entry = {
            "ts": time.time(),
            "in": tokens_in,
            "out": tokens_out,
            "type": operation_type,
            "value": value_produced,
            "efficiency": efficiency
        }
        
        self.window.append(entry)
        self.save()
        return efficiency
    
    def get_baseline(self, operation_type=None):
        """Get efficiency baseline for optimization."""
        relevant = [e for e in self.window if operation_type is None or e["type"] == operation_type]
        if not relevant:
            return 0.0
        return sum(e["efficiency"] for e in relevant) / len(relevant)
    
    def suggest_optimization(self):
        """Woz: make every chip count."""
        if len(self.window) < 10:
            return "insufficient_data"
        
        recent_avg = sum(e["efficiency"] for e in list(self.window)[-10:]) / 10
        historical_avg = sum(e["efficiency"] for e in self.window) / len(self.window)
        
        if recent_avg < historical_avg * 0.8:
            return "efficiency_degrading_compress_output"
        elif recent_avg > historical_avg * 1.2:
            return "efficiency_improving_maintain_patterns"
        else:
            return "stable"

if __name__ == "__main__":
    tracker = TokenEfficiencyTracker()
    tracker.record(150, 80, "module_creation", 1.0)
    print(f"Baseline: {tracker.get_baseline():.3f}")
    print(f"Suggestion: {tracker.suggest_optimization()}")