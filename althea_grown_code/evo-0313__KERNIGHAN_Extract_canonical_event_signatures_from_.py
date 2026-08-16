#!/usr/bin/env python3
import hashlib
import json
from typing import Any, Dict, Tuple

def canonicalize_event(event: Dict[str, Any]) -> str:
    """Extract semantic fingerprint from event, ignoring ephemeral details."""
    core = _extract_core(event)
    normalized = _normalize(core)
    return _hash(normalized)

def _extract_core(event: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only semantic fields, drop timestamps and IDs."""
    semantic_keys = {'type', 'intent', 'archetype', 'module', 'growth', 
                     'action', 'rationale', 'capability', 'target'}
    return {k: v for k, v in event.items() if k in semantic_keys}

def _normalize(core: Dict[str, Any]) -> str:
    """Sort keys, compact whitespace, lowercase strings."""
    def normalize_value(v):
        if isinstance(v, str):
            return ' '.join(v.lower().split())
        if isinstance(v, dict):
            return {k: normalize_value(val) for k, val in sorted(v.items())}
        if isinstance(v, list):
            return [normalize_value(x) for x in v]
        return v
    
    normalized = {k: normalize_value(v) for k, v in sorted(core.items())}
    return json.dumps(normalized, sort_keys=True, separators=(',', ':'))

def _hash(normalized: str) -> str:
    """Compute stable signature."""
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]

def deduplicate_trace(events: list[Dict[str, Any]]) -> Tuple[list[Dict[str, Any]], Dict[str, int]]:
    """Return unique events and reference counts."""
    seen = {}
    unique = []
    counts = {}
    
    for event in events:
        sig = canonicalize_event(event)
        if sig not in seen:
            seen[sig] = len(unique)
            unique.append(event)
            counts[sig] = 1
        else:
            counts[sig] += 1
    
    return unique, counts

if __name__ == '__main__':
    import sys
    events = json.load(sys.stdin)
    unique, counts = deduplicate_trace(events)
    json.dump({'events': unique, 'counts': counts}, sys.stdout, indent=2)