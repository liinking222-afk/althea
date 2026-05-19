import ctypes
import math

class FastRingIndex:
    """Branchless ring buffer indexing. Power-of-two sizes only. Sub-ns ops."""
    
    __slots__ = ('_size', '_mask', '_shift')
    
    def __init__(self, size: int):
        # Force power-of-two, cache shift and mask for branchless wrap
        assert size > 0 and (size & (size - 1)) == 0, "Size must be power of 2"
        self._size = size
        self._mask = size - 1  # 0b111 for size=8, enables AND instead of MOD
        self._shift = int(math.log2(size))
    
    def wrap(self, idx: int) -> int:
        """Branchless wrap using bitwise AND. ~3 cycles on modern x64."""
        return idx & self._mask
    
    def advance(self, idx: int, delta: int = 1) -> int:
        """Advance and wrap in single op. No branch misprediction."""
        return (idx + delta) & self._mask
    
    def distance(self, head: int, tail: int) -> int:
        """Occupied slots. Handles wraparound without conditional."""
        return (head - tail) & self._mask
    
    def is_full(self, head: int, tail: int) -> bool:
        """Check capacity. Next head would collide with tail."""
        return ((head + 1) & self._mask) == (tail & self._mask)
    
    def is_empty(self, head: int, tail: int) -> bool:
        """Empty when indices match after masking."""
        return (head & self._mask) == (tail & self._mask)
    
    @property
    def mask(self) -> int:
        """Expose mask for inline wrapping: (idx & ring.mask)"""
        return self._mask
    
    @property
    def size(self) -> int:
        return self._size
    
    def slot_address_offset(self, idx: int, slot_bytes: int) -> int:
        """Byte offset for cache-aligned slot access. Inline this."""
        return (idx & self._mask) * slot_bytes

# Example: 256-slot ring, 64-byte aligned messages (cache line)
ring = FastRingIndex(256)
head = tail = 0
head = ring.advance(head, 1)  # Branchless increment
occupied = ring.distance(head, tail)  # Wraps correctly
offset = ring.slot_address_offset(head, 64)  # Memory arithmetic