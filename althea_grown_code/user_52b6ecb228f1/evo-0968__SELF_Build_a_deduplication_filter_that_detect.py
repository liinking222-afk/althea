#!/usr/bin/env python3
"""
AUTOSYNTH Deduplication Filter
Tracks recent AUTOSYNTH creations and blocks redundant pattern synthesis
"""

import json
import os
import time
from pathlib import Path
from hashlib import sha256

CACHE_FILE = Path.home() / ".althea" / "autosynth_cache.json"
CACHE_TTL = 3600  # 1 hour window for dedup
MAX_CACHE_SIZE = 500

def load_cache():
    """Load the deduplication cache"""
    if not CACHE_FILE.exists():
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_cache(cache):
    """Persist the cache to disk"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def clean_cache(cache):
    """Remove stale entries beyond TTL"""
    now = time.time()
    return {k: v for k, v in cache.items() if now - v['timestamp'] < CACHE_TTL}

def pattern_signature(pattern_name, context_hash=None):
    """Generate unique signature for a pattern synthesis request"""
    sig_input = f"{pattern_name}:{context_hash or 'default'}"
    return sha256(sig_input.encode()).hexdigest()[:16]

def should_synthesize(pattern_name, context_hash=None):
    """Returns True if synthesis should proceed, False if redundant"""
    cache = clean_cache(load_cache())
    sig = pattern_signature(pattern_name, context_hash)
    
    if sig in cache:
        return False
    
    # Limit cache size
    if len(cache) >= MAX_CACHE_SIZE:
        oldest = min(cache.items(), key=lambda x: x[1]['timestamp'])
        del cache[oldest[0]]
    
    cache[sig] = {
        'pattern': pattern_name,
        'timestamp': time.time()
    }
    save_cache(cache)
    return True

if __name__ == "__main__":
    import sys
    pattern = sys.argv[1] if len(sys.argv) > 1 else "test-pattern"
    context = sys.argv[2] if len(sys.argv) > 2 else None
    
    if should_synthesize(pattern, context):
        print(f"PROCEED: {pattern}")
        sys.exit(0)
    else:
        print(f"BLOCKED: {pattern} (redundant)")
        sys.exit(1)