#!/usr/bin/env python3
"""one_thing.py - Show the ONE metric that matters right now"""

import sys
import json
from typing import Any, Dict

def extract_signal(data: Dict[str, Any]) -> tuple[str, Any]:
    """Returns (metric_name, value) for the single most important signal."""
    
    # Priority order: what changes most meaningfully
    if "memory_count" in data:
        return ("memory_count", data["memory_count"])
    
    if "size" in data and isinstance(data["size"], str):
        w, h = map(int, data["size"].split("x"))
        return ("viewport_area", w * h)
    
    if "online" in data:
        return ("online", data["online"])
    
    # Fallback: first non-metadata key
    for key in sorted(data.keys()):
        if key not in ["source", "tab", "timestamp"]:
            return (key, data[key])
    
    return ("status", "empty")

def format_output(metric: str, value: Any) -> str:
    """One metric. One line."""
    return f"{metric}: {value}"

def main():
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
    else:
        data = json.load(sys.stdin)
    
    metric, value = extract_signal(data)
    print(format_output(metric, value))

if __name__ == "__main__":
    main()