#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from datetime import datetime

REGISTRY_PATH = Path("/tmp/althea_modules.txt")

def register_module(module_id, module_type, description):
    """Register a module as a single line: timestamp|id|type|description"""
    timestamp = datetime.utcnow().isoformat()
    line = f"{timestamp}|{module_id}|{module_type}|{description}\n"
    with open(REGISTRY_PATH, "a") as f:
        f.write(line)
    return line.strip()

def list_modules(filter_type=None):
    """List modules as plain text stream, optionally filtered by type"""
    if not REGISTRY_PATH.exists():
        return
    with open(REGISTRY_PATH, "r") as f:
        for line in f:
            if filter_type:
                parts = line.strip().split("|", 3)
                if len(parts) >= 3 and parts[2] == filter_type:
                    print(line.strip())
            else:
                print(line.strip())

def search_modules(query):
    """Grep-like search through module registry"""
    if not REGISTRY_PATH.exists():
        return
    with open(REGISTRY_PATH, "r") as f:
        for line in f:
            if query.lower() in line.lower():
                print(line.strip())

def count_by_type():
    """Count modules by type using awk-like field processing"""
    if not REGISTRY_PATH.exists():
        return
    counts = {}
    with open(REGISTRY_PATH, "r") as f:
        for line in f:
            parts = line.strip().split("|", 3)
            if len(parts) >= 3:
                module_type = parts[2]
                counts[module_type] = counts.get(module_type, 0) + 1
    for mtype, count in sorted(counts.items()):
        print(f"{count}\t{mtype}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    
    if cmd == "register" and len(sys.argv) == 5:
        print(register_module(sys.argv[2], sys.argv[3], sys.argv[4]))
    elif cmd == "list":
        filter_type = sys.argv[2] if len(sys.argv) > 2 else None
        list_modules(filter_type)
    elif cmd == "search" and len(sys.argv) > 2:
        search_modules(sys.argv[2])
    elif cmd == "count":
        count_by_type()