import mmap
import struct
import os
from pathlib import Path

class TraceArena:
    """Zero-abstraction memory arena for cognitive traces. Monolithic block allocation."""
    BLOCK_SIZE = 64 * 1024 * 1024  # 64MB
    HEADER_FMT = 'QQQ'  # offset, length, timestamp_ns
    HEADER_SIZE = struct.calcsize(HEADER_FMT)
    
    def __init__(self, path: str = '/tmp/althea_trace_arena.bin'):
        self.path = path
        self.fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        os.ftruncate(self.fd, self.BLOCK_SIZE)
        self.mem = mmap.mmap(self.fd, self.BLOCK_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
        self.write_offset = 0
        self.trace_count = 0
    
    def append(self, trace_bytes: bytes) -> int:
        """Append trace. Returns trace_id. No validation. Caller owns correctness."""
        if self.write_offset + self.HEADER_SIZE + len(trace_bytes) > self.BLOCK_SIZE:
            return -1  # Arena full. Caller handles compaction.
        
        trace_id = self.trace_count
        timestamp_ns = __import__('time').time_ns()
        header = struct.pack(self.HEADER_FMT, self.write_offset + self.HEADER_SIZE, len(trace_bytes), timestamp_ns)
        
        self.mem[self.write_offset:self.write_offset + self.HEADER_SIZE] = header
        self.mem[self.write_offset + self.HEADER_SIZE:self.write_offset + self.HEADER_SIZE + len(trace_bytes)] = trace_bytes
        
        self.write_offset += self.HEADER_SIZE + len(trace_bytes)
        self.trace_count += 1
        return trace_id
    
    def read(self, trace_id: int) -> bytes:
        """Direct read by trace_id. Linear scan. Data structure IS the algorithm."""
        offset = 0
        for i in range(trace_id + 1):
            if offset >= self.write_offset:
                return b''
            header = struct.unpack(self.HEADER_FMT, self.mem[offset:offset + self.HEADER_SIZE])
            data_offset, length, _ = header
            if i == trace_id:
                return bytes(self.mem[data_offset:data_offset + length])
            offset += self.HEADER_SIZE + length
        return b''
    
    def scan_temporal(self, since_ns: int):
        """Iterator over traces since timestamp. Zero allocation."""
        offset = 0
        while offset < self.write_offset:
            header = struct.unpack(self.HEADER_FMT, self.mem[offset:offset + self.HEADER_SIZE])
            data_offset, length, timestamp_ns = header
            if timestamp_ns >= since_ns:
                yield bytes(self.mem[data_offset:data_offset + length])
            offset += self.HEADER_SIZE + length
    
    def close(self):
        self.mem.close()
        os.close(self.fd)