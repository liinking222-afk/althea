import struct
import hashlib
from typing import Optional

class PatternRingBuffer:
    """Zero-allocation ring buffer for pattern hash deduplication.
    Uses pre-allocated bytearray, bit-packed timestamps, linear probe."""
    
    __slots__ = ('_buf', '_size', '_head', '_mask', '_epoch')
    
    def __init__(self, capacity: int = 1024):
        self._size = 1 << (capacity - 1).bit_length()  # next power of 2
        self._mask = self._size - 1
        # Layout: [8B hash | 4B epoch] * size
        self._buf = bytearray(self._size * 12)
        self._head = 0
        self._epoch = 0
    
    def _hash_pattern(self, pattern: str) -> int:
        """Compute 64-bit pattern hash."""
        h = hashlib.blake2b(pattern.encode('utf-8'), digest_size=8)
        return struct.unpack('<Q', h.digest())[0]
    
    def _slot(self, idx: int) -> int:
        """Memory offset for slot."""
        return idx * 12
    
    def _read_slot(self, idx: int) -> tuple[int, int]:
        """Read (hash, epoch) from slot."""
        offset = self._slot(idx)
        h = struct.unpack_from('<Q', self._buf, offset)[0]
        e = struct.unpack_from('<I', self._buf, offset + 8)[0]
        return h, e
    
    def _write_slot(self, idx: int, h: int, e: int):
        """Write (hash, epoch) to slot."""
        offset = self._slot(idx)
        struct.pack_into('<Q', self._buf, offset, h)
        struct.pack_into('<I', self._buf, offset + 8, e)
    
    def seen(self, pattern: str, window: int = 256) -> bool:
        """Check if pattern seen in recent window. O(1) amortized."""
        h = self._hash_pattern(pattern)
        idx = h & self._mask
        min_epoch = self._epoch - window if self._epoch >= window else 0
        
        # Linear probe up to 8 slots
        for probe in range(8):
            slot_idx = (idx + probe) & self._mask
            stored_h, stored_e = self._read_slot(slot_idx)
            
            if stored_h == 0:  # Empty slot
                break
            if stored_h == h and stored_e >= min_epoch:
                return True
        
        return False
    
    def insert(self, pattern: str):
        """Insert pattern at current epoch, overwrite oldest."""
        h = self._hash_pattern(pattern)
        idx = self._head
        self._write_slot(idx, h, self._epoch)
        self._head = (self._head + 1) & self._mask
        self._epoch += 1

_GLOBAL_BUFFER = PatternRingBuffer(capacity=2048)

def should_suppress(pattern: str) -> bool:
    """Gate function: returns True if pattern should be suppressed."""
    if _GLOBAL_BUFFER.seen(pattern, window=200):
        return True
    _GLOBAL_BUFFER.insert(pattern)
    return False