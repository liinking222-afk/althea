import struct
import mmap
from typing import Optional

class PatternFrequencyRing:
    """Cache-aligned ring buffer for sub-ms pattern frequency queries.
    Uses 64-byte cache lines, power-of-2 sizing, and inline hash for zero-chase lookups."""
    
    def __init__(self, capacity: int = 1024):
        self.cap = 1 << (capacity - 1).bit_length()  # next power of 2
        self.mask = self.cap - 1  # modulo via bitwise AND
        self.head = 0
        # 16 bytes per entry: 8-byte hash + 4-byte count + 4-byte timestamp
        self.buf = mmap.mmap(-1, self.cap * 16, prot=mmap.PROT_READ | mmap.PROT_WRITE)
        self.decay_shift = 10  # divide by 1024 per window
        
    def _hash(self, pattern: str) -> int:
        """FNV-1a inline - 3 ops per byte, excellent avalanche."""
        h = 0xcbf29ce484222325
        for b in pattern.encode('utf-8'):
            h = ((h ^ b) * 0x100000001b3) & 0xffffffffffffffff
        return h
    
    def record(self, pattern: str, timestamp: int) -> int:
        """O(1) record with linear probing. Returns observed frequency."""
        h = self._hash(pattern)
        idx = (h & self.mask) * 16
        
        # Linear probe - cache-friendly sequential access
        for probe in range(8):  # max 8 probes before evict
            pos = ((h + probe) & self.mask) * 16
            stored_hash = struct.unpack_from('Q', self.buf, pos)[0]
            
            if stored_hash == 0 or stored_hash == h:
                # Hit or empty slot
                count, last_ts = struct.unpack_from('II', self.buf, pos + 8)
                
                # Exponential decay based on timestamp delta
                delta = timestamp - last_ts
                if delta > 0 and count > 0:
                    count = max(1, count - (delta >> self.decay_shift))
                
                count += 1
                struct.pack_into('QII', self.buf, pos, h, count, timestamp)
                return count
        
        # Evict at original hash position
        struct.pack_into('QII', self.buf, idx, h, 1, timestamp)
        return 1
    
    def query(self, pattern: str) -> int:
        """O(1) frequency lookup. Returns 0 if not found."""
        h = self._hash(pattern)
        for probe in range(8):
            pos = ((h + probe) & self.mask) * 16
            stored_hash = struct.unpack_from('Q', self.buf, pos)[0]
            if stored_hash == h:
                return struct.unpack_from('I', self.buf, pos + 8)[0]
            if stored_hash == 0:
                break
        return 0
    
    def should_suppress(self, pattern: str, threshold: int = 3) -> bool:
        """Inline decision: suppress if frequency exceeds threshold."""
        return self.query(pattern) >= threshold

# Global singleton - zero allocation on module calls
_RING = PatternFrequencyRing(2048)

def check_autosynth_redundancy(pattern_name: str, timestamp_ms: int) -> bool:
    """Returns True if pattern should be suppressed due to redundancy."""
    freq = _RING.record(pattern_name, timestamp_ms)
    return freq > 2  # suppress after 3rd occurrence in decay window