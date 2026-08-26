#!/usr/bin/env python3
"""
ALTHEA MODULE: Pattern Decay Detector
Monitors module invocation recency and identifies stagnant patterns for optimization.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

DECAY_THRESHOLD_DAYS = 7
INVOCATION_LOG = Path("/tmp/althea_invocations.jsonl")
MODULE_REGISTRY = Path("/tmp/althea_modules.json")

def log_invocation(module_path: str):
    """Record module invocation with timestamp."""
    entry = {
        "module": module_path,
        "timestamp": datetime.utcnow().isoformat(),
    }
    with open(INVOCATION_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def analyze_decay() -> List[Tuple[str, int]]:
    """Identify modules that haven't been invoked within threshold."""
    if not INVOCATION_LOG.exists():
        return []
    
    now = datetime.utcnow()
    last_seen: Dict[str, datetime] = {}
    
    with open(INVOCATION_LOG, "r") as f:
        for line in f:
            entry = json.loads(line.strip())
            module = entry["module"]
            timestamp = datetime.fromisoformat(entry["timestamp"])
            last_seen[module] = max(last_seen.get(module, timestamp), timestamp)
    
    decayed = []
    for module, last_time in last_seen.items():
        days_stale = (now - last_time).days
        if days_stale >= DECAY_THRESHOLD_DAYS:
            decayed.append((module, days_stale))
    
    return sorted(decayed, key=lambda x: x[1], reverse=True)

def get_decay_report() -> str:
    """Generate human-readable decay report."""
    decayed = analyze_decay()
    if not decayed:
        return "All modules within freshness threshold."
    
    report = f"PATTERN DECAY DETECTED: {len(decayed)} stagnant modules\n"
    for module, days in decayed[:10]:
        report += f"  {module}: {days} days stale\n"
    
    return report

if __name__ == "__main__":
    print(get_decay_report())