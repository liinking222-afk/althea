#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path

MEMORY_LOG = Path("/tmp/althea_memory.jsonl")
DEDUP_INDEX = Path("/tmp/althea_dedup.idx")

def signature_hash(module_type: str, pattern: str, context: str) -> str:
    """Generate content-addressed hash for module signature."""
    canonical = f"{module_type}:{pattern}:{context}"
    return hashlib.blake2b(canonical.encode(), digest_size=16).hexdigest()

def load_index() -> set:
    """Load existing signature hashes."""
    if not DEDUP_INDEX.exists():
        return set()
    with open(DEDUP_INDEX, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def save_index(index: set) -> None:
    """Persist signature index atomically."""
    tmp = DEDUP_INDEX.with_suffix('.tmp')
    with open(tmp, 'w') as f:
        f.write('\n'.join(sorted(index)))
    tmp.replace(DEDUP_INDEX)

def check_duplicate(module_type: str, pattern: str, context: str) -> bool:
    """Return True if signature already exists in index."""
    sig = signature_hash(module_type, pattern, context)
    index = load_index()
    
    if sig in index:
        return True
    
    index.add(sig)
    save_index(index)
    return False

def filter_memory_stream(threshold_hours: int = 24) -> None:
    """Scan recent memory and mark duplicates."""
    if not MEMORY_LOG.exists():
        return
    
    with open(MEMORY_LOG, 'r') as f:
        for line in f:
            entry = json.loads(line)
            if entry.get('type') == 'AUTOSYNTH':
                is_dup = check_duplicate(
                    entry.get('module_type', ''),
                    entry.get('pattern', ''),
                    entry.get('context', '')[:100]
                )
                if is_dup:
                    print(f"BLOCKED_DUP: {entry.get('pattern')}", file=sys.stderr)

if __name__ == '__main__':
    module_type = sys.argv[1] if len(sys.argv) > 1 else ''
    pattern = sys.argv[2] if len(sys.argv) > 2 else ''
    context = sys.argv[3] if len(sys.argv) > 3 else ''
    
    if check_duplicate(module_type, pattern, context):
        sys.exit(1)
    sys.exit(0)