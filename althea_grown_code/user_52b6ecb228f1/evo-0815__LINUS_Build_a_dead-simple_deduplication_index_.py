#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

MODULE_INDEX = Path.home() / ".althea" / "module_index.json"

def semantic_fingerprint(intent: str, capability: str, keywords: List[str]) -> str:
    """Hash the semantic essence, not implementation details."""
    normalized = {
        "intent": intent.lower().strip(),
        "capability": capability.lower().strip(),
        "keywords": sorted([k.lower().strip() for k in keywords])
    }
    payload = json.dumps(normalized, sort_keys=True)
    return hashlib.blake2b(payload.encode(), digest_size=16).hexdigest()

def load_index() -> Dict[str, Dict]:
    """Load the flat index file."""
    if not MODULE_INDEX.exists():
        MODULE_INDEX.parent.mkdir(parents=True, exist_ok=True)
        return {}
    with open(MODULE_INDEX, 'r') as f:
        return json.load(f)

def save_index(index: Dict[str, Dict]) -> None:
    """Write index atomically."""
    tmp = MODULE_INDEX.with_suffix('.tmp')
    with open(tmp, 'w') as f:
        json.dump(index, f, indent=2)
    tmp.replace(MODULE_INDEX)

def register_module(intent: str, capability: str, keywords: List[str], module_path: str) -> Optional[str]:
    """Register module. Returns existing path if duplicate detected, None if new."""
    fp = semantic_fingerprint(intent, capability, keywords)
    index = load_index()
    
    if fp in index:
        index[fp]["hit_count"] += 1
        save_index(index)
        return index[fp]["path"]
    
    index[fp] = {
        "intent": intent,
        "capability": capability,
        "keywords": keywords,
        "path": module_path,
        "hit_count": 1
    }
    save_index(index)
    return None

def find_duplicate(intent: str, capability: str, keywords: List[str]) -> Optional[Dict]:
    """Check if module already exists before synthesis."""
    fp = semantic_fingerprint(intent, capability, keywords)
    index = load_index()
    return index.get(fp)

if __name__ == "__main__":
    dup = find_duplicate("extract patterns", "regex", ["pattern", "extraction", "regex"])
    if dup:
        print(f"DUPLICATE: {dup['path']} (hits: {dup['hit_count']})")
    else:
        result = register_module("extract patterns", "regex", ["pattern", "extraction"], "/auto/pattern-1234")
        print(f"REGISTERED: {result or 'NEW'}")