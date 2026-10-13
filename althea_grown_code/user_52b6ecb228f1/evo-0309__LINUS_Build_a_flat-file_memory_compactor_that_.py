#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
from collections import defaultdict

MEMORY_FILE = Path("/tmp/althea_memory.jsonl")
COMPACT_FILE = Path("/tmp/althea_memory_compact.jsonl")

def semantic_hash(entry):
    """Hash based on actual semantic content, not metadata"""
    content = {
        "type": entry.get("type"),
        "module": entry.get("module"),
        "intent": entry.get("intent"),
        "rationale": entry.get("rationale", "")[:100]  # truncate variable parts
    }
    return hashlib.blake2b(json.dumps(content, sort_keys=True).encode(), digest_size=16).hexdigest()

def compact_memory():
    if not MEMORY_FILE.exists():
        return
    
    # Single pass: read, hash, dedupe
    canonical = {}  # hash -> (entry, count, first_seen, last_seen)
    
    for line in MEMORY_FILE.read_text().strip().split('\n'):
        if not line:
            continue
        entry = json.loads(line)
        h = semantic_hash(entry)
        
        if h in canonical:
            _, count, first, _ = canonical[h]
            canonical[h] = (entry, count + 1, first, entry.get("timestamp", ""))
        else:
            ts = entry.get("timestamp", "")
            canonical[h] = (entry, 1, ts, ts)
    
    # Write compacted: one entry per semantic unit with metadata
    with COMPACT_FILE.open('w') as f:
        for h, (entry, count, first, last) in canonical.items():
            entry["_refcount"] = count
            entry["_first_seen"] = first
            entry["_last_seen"] = last
            entry["_semantic_hash"] = h
            f.write(json.dumps(entry) + '\n')
    
    orig_size = MEMORY_FILE.stat().st_size
    comp_size = COMPACT_FILE.stat().st_size
    return len(canonical), orig_size, comp_size

if __name__ == "__main__":
    result = compact_memory()
    if result:
        unique, orig, comp = result
        print(f"Compacted to {unique} unique entries: {orig} -> {comp} bytes")