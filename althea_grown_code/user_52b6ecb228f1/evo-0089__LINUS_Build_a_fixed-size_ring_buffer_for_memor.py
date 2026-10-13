#!/usr/bin/env python3
import struct
from collections import namedtuple

RING_SIZE = 1024
ENTRY_SIZE = 16  # timestamp(8) + delta(4) + flags(4)

MemDelta = namedtuple('MemDelta', ['ts', 'delta', 'flags'])

class MemoryDeltaRing:
    """Fixed-size ring buffer storing only memory deltas, not full states."""
    
    def __init__(self):
        self.buf = bytearray(RING_SIZE * ENTRY_SIZE)
        self.head = 0
        self.count = 0
        self.baseline = 0
    
    def push(self, timestamp, mem_bytes):
        """Store delta from baseline, not absolute value."""
        delta = mem_bytes - self.baseline
        flags = (1 if delta > 0 else 0) | (2 if abs(delta) > 1000 else 0)
        
        offset = (self.head % RING_SIZE) * ENTRY_SIZE
        struct.pack_into('!Qii', self.buf, offset, timestamp, delta, flags)
        
        self.head += 1
        self.count = min(self.count + 1, RING_SIZE)
        self.baseline = mem_bytes
    
    def get(self, idx):
        """Retrieve delta entry by index (0 = oldest)."""
        if idx >= self.count:
            return None
        
        actual_idx = (self.head - self.count + idx) % RING_SIZE
        offset = actual_idx * ENTRY_SIZE
        ts, delta, flags = struct.unpack_from('!Qii', self.buf, offset)
        return MemDelta(ts, delta, flags)
    
    def reconstruct_absolute(self, start_baseline):
        """Reconstruct absolute values from deltas."""
        values = []
        current = start_baseline
        for i in range(self.count):
            entry = self.get(i)
            current += entry.delta
            values.append((entry.ts, current, entry.flags))
        return values
    
    def memory_footprint(self):
        """Always constant."""
        return len(self.buf)
    
    def compression_ratio(self):
        """Estimate vs storing full 8-byte values."""
        full_size = self.count * 8
        return full_size / len(self.buf) if full_size > 0 else 0.0

if __name__ == '__main__':
    ring = MemoryDeltaRing()
    import time
    base = 20000
    for i in range(2000):
        ring.push(int(time.time() * 1e9), base + (i * 100) % 500)
    print(f"Footprint: {ring.memory_footprint()} bytes (constant)")
    print(f"Compression: {ring.compression_ratio():.2f}x")