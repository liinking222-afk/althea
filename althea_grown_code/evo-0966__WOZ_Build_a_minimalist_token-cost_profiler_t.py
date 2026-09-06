#!/usr/bin/env python3
"""
/autonomous-token-profiler
Woz-style constraint tracking: make every token count by knowing what costs what.
"""
import json
import os
import time
from pathlib import Path
from typing import Optional

STATE_FILE = Path.home() / ".althea" / "token_profile.json"

def load_state() -> dict:
    """Load token profile state or return empty dict."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            return {}
    return {}

def save_state(state: dict):
    """Atomically save token profile state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)

def record_invocation(module: str, tokens_in: int, tokens_out: int, budget: Optional[int] = None):
    """Record a module invocation with token costs."""
    state = load_state()
    
    if module not in state:
        state[module] = {
            "invocations": 0,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_tokens": 0,
            "first_seen": time.time(),
            "last_seen": time.time()
        }
    
    m = state[module]
    m["invocations"] += 1
    m["total_tokens_in"] += tokens_in
    m["total_tokens_out"] += tokens_out
    m["total_tokens"] += (tokens_in + tokens_out)
    m["last_seen"] = time.time()
    
    if budget:
        m["last_budget"] = budget
        m["last_efficiency"] = round((tokens_in + tokens_out) / budget, 4)
    
    save_state(state)

def get_top_consumers(n: int = 10) -> list:
    """Return top N modules by total token consumption."""
    state = load_state()
    ranked = sorted(state.items(), key=lambda x: x[1]["total_tokens"], reverse=True)
    return ranked[:n]

def get_profile(module: str) -> Optional[dict]:
    """Get profile for specific module."""
    return load_state().get(module)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "top":
        for mod, data in get_top_consumers(15):
            print(f"{mod:40s} {data['total_tokens']:8d} tok ({data['invocations']:4d} calls)")