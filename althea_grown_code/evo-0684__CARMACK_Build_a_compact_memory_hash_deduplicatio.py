import time
from typing import List, Tuple

# FNV-1a constants - prime multiplication for avalanche
FNV_PRIME = 0x01000193
FNV_OFFSET = 0x811c9dc5

# Cache-line aligned ring buffer size (power of 2 for bitmask)
FINGERPRINT_SLOTS = 512
SLOT_MASK = FINGERPRINT_SLOTS - 1

# Sliding window in seconds
DEDUP_WINDOW = 3600

# Compact fingerprint storage: (hash32, timestamp_float)
_fingerprints: List[Tuple[int, float]] = [(0, 0.0)] * FINGERPRINT_SLOTS
_write_cursor = 0

def fnv1a_hash(text: str) -> int:
    """FNV-1a hash - fast non-crypto hash optimized for distribution"""
    h = FNV_OFFSET
    for byte in text.encode('utf-8'):
        h ^= byte
        h = (h * FNV_PRIME) & 0xFFFFFFFF  # Keep 32-bit, avoid bigint allocation
    return h

def is_duplicate(memory_key: str) -> bool:
    """Check if memory_key is duplicate within sliding window - O(1) amortized"""
    global _write_cursor
    
    now = time.time()
    cutoff = now - DEDUP_WINDOW
    fingerprint = fnv1a_hash(memory_key)
    
    # Linear probe from hash position - cache-friendly sequential access
    start_slot = fingerprint & SLOT_MASK
    for offset in range(32):  # Max 32 probes to stay sub-millisecond
        slot = (start_slot + offset) & SLOT_MASK
        stored_hash, stored_time = _fingerprints[slot]
        
        if stored_hash == fingerprint and stored_time >= cutoff:
            return True  # Hot path: duplicate found
        if stored_time < cutoff or stored_hash == 0:
            break  # Slot expired or empty
    
    # Insert new fingerprint at write cursor (FIFO eviction)
    _fingerprints[_write_cursor] = (fingerprint, now)
    _write_cursor = (_write_cursor + 1) & SLOT_MASK
    
    return False

def dedupe_memories(memory_keys: List[str]) -> List[str]:
    """Filter list to unique memories only - tight loop for batch processing"""
    unique = []
    for key in memory_keys:
        if not is_duplicate(key):
            unique.append(key)
    return unique