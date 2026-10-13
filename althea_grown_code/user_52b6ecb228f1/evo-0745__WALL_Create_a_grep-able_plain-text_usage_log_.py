#!/usr/bin/env python3
"""
Module: usage_log
Archetype: WALL - plain text, grep-able, awk-able usage tracking
"""

import os
import time
from datetime import datetime
from pathlib import Path

LOG_DIR = Path.home() / ".althea" / "logs"
USAGE_LOG = LOG_DIR / "module_usage.log"


def ensure_log_exists():
    """Ensure log directory and file exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not USAGE_LOG.exists():
        USAGE_LOG.touch()


def log_invocation(module_name: str, **params):
    """
    Log a module invocation as a single pipe-delimited line.
    Format: timestamp|module|param1=value1|param2=value2|...
    """
    ensure_log_exists()
    
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    param_str = "|".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
    
    line = f"{ts}|{module_name}"
    if param_str:
        line += f"|{param_str}"
    line += "\n"
    
    with open(USAGE_LOG, "a") as f:
        f.write(line)


def query_log(module_name=None, since_hours=None, limit=100):
    """
    Query usage log with optional filters.
    Returns list of parsed records as dicts.
    """
    ensure_log_exists()
    
    records = []
    cutoff = time.time() - (since_hours * 3600) if since_hours else 0
    
    with open(USAGE_LOG, "r") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) < 2:
                continue
            
            ts_str, mod = parts[0], parts[1]
            
            if module_name and mod != module_name:
                continue
            
            ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").timestamp()
            if ts < cutoff:
                continue
            
            params = {}
            for part in parts[2:]:
                if "=" in part:
                    k, v = part.split("=", 1)
                    params[k] = v
            
            records.append({"timestamp": ts_str, "module": mod, "params": params})
            
            if len(records) >= limit:
                break
    
    return records[-limit:]


if __name__ == "__main__":
    # Example usage
    log_invocation("weather-inquiry", location="San Francisco", units="metric")
    log_invocation("tabular-analysis", file="data.csv", operation="summary")
    print(f"Log: {USAGE_LOG}")
    print("Recent entries:", query_log(limit=5))