import mmap
import struct
import os
from pathlib import Path

class MemoryByteRing:
    """Fixed-size ring buffer for memory sizes. mmap-backed, lock-free reads."""
    
    ENTRY_SIZE = 12  # timestamp(u64) + size(u32)
    
    def __init__(self, capacity=1024, path=None):
        self.capacity = capacity
        self.size = capacity * self.ENTRY_SIZE + 8  # +8 for head index
        self.path = path or Path.home() / ".althea" / "mem_ring.dat"
        self.path.parent.mkdir(exist_ok=True)
        
        if not self.path.exists():
            with open(self.path, 'wb') as f:
                f.write(b'\x00' * self.size)
        
        self.fd = os.open(self.path, os.O_RDWR)
        self.mem = mmap.mmap(self.fd, self.size)
    
    def push(self, timestamp, byte_count):
        """Write entry. O(1). Overwrites oldest."""
        head = struct.unpack_from('Q', self.mem, 0)[0]
        offset = 8 + (head % self.capacity) * self.ENTRY_SIZE
        struct.pack_into('QI', self.mem, offset, timestamp, byte_count)
        struct.pack_into('Q', self.mem, 0, head + 1)
        self.mem.flush()
    
    def scan_anomalies(self, threshold_ratio=1.5):
        """Detect sudden size jumps. Returns list of (ts, size, delta_ratio)."""
        head = struct.unpack_from('Q', self.mem, 0)[0]
        count = min(head, self.capacity)
        if count < 2:
            return []
        
        anomalies = []
        prev_size = None
        
        for i in range(count):
            idx = (head - count + i) % self.capacity
            offset = 8 + idx * self.ENTRY_SIZE
            ts, size = struct.unpack_from('QI', self.mem, offset)
            
            if prev_size and size > prev_size * threshold_ratio:
                anomalies.append((ts, size, size / prev_size))
            prev_size = size
        
        return anomalies
    
    def get_trend(self):
        """Returns (mean, stddev, min, max) of recent sizes."""
        head = struct.unpack_from('Q', self.mem, 0)[0]
        count = min(head, self.capacity)
        if count == 0:
            return (0, 0, 0, 0)
        
        sizes = []
        for i in range(count):
            idx = (head - count + i) % self.capacity
            offset = 8 + idx * self.ENTRY_SIZE + 8
            size = struct.unpack_from('I', self.mem, offset)[0]
            sizes.append(size)
        
        mean = sum(sizes) / count
        var = sum((x - mean) ** 2 for x in sizes) / count
        return (mean, var ** 0.5, min(sizes), max(sizes))
    
    def close(self):
        self.mem.close()
        os.close(self.fd)