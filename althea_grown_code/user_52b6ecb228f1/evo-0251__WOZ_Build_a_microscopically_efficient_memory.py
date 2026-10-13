#!/usr/bin/env python3
import sys
import struct
from collections import defaultdict

def woz_hash(text: str) -> int:
    """Ultra-compact FNV-1a hash variant: every byte counts."""
    h = 0xcbf29ce484222325
    for byte in text.encode('utf-8', errors='ignore'):
        h ^= byte
        h = (h * 0x100000001b3) & 0xffffffffffffffff
    return h

def extract_signature(line: str) -> tuple:
    """Minimal extraction: type + action fingerprint."""
    parts = line.strip().split(maxsplit=2)
    if len(parts) < 2:
        return (0, 0)
    
    marker = parts[0]
    content = parts[-1] if len(parts) > 1 else ""
    
    type_hash = woz_hash(marker) & 0xFFFF
    content_hash = woz_hash(content[:120])
    
    return (type_hash, content_hash)

def main():
    """Streaming fingerprint deduplicator with drift detection."""
    seen = defaultdict(int)
    drift_threshold = 3
    unique_count = 0
    
    for line in sys.stdin:
        if not line.strip():
            continue
            
        sig = extract_signature(line)
        compact = struct.pack('HQ', sig[0], sig[1])
        
        seen[compact] += 1
        
        if seen[compact] == 1:
            unique_count += 1
            print(f"NEW {compact.hex()} {line.strip()[:60]}")
        elif seen[compact] == drift_threshold:
            print(f"DRIFT {compact.hex()} cnt={seen[compact]}")
    
    print(f"\nSTATS: {unique_count} unique / {len(seen)} patterns / {sum(seen.values())} total", 
          file=sys.stderr)

if __name__ == "__main__":
    main()