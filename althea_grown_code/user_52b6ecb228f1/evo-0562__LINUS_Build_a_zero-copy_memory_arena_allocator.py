import mmap
import struct
from typing import Optional, Tuple

class TemporalArena:
    """Zero-copy arena for timestamped cognitive events. Monolithic block, no GC thrash."""
    
    HEADER_SIZE = 24  # timestamp(8) + size(4) + type(4) + flags(4) + next(4)
    BLOCK_SIZE = 1024 * 1024  # 1MB blocks
    
    def __init__(self, max_blocks: int = 64):
        self.blocks = [mmap.mmap(-1, self.BLOCK_SIZE) for _ in range(max_blocks)]
        self.current_block = 0
        self.offset = 0
        self.head = None
        
    def alloc(self, timestamp: float, event_type: int, data: bytes) -> int:
        """Allocate entry, return offset. No fragmentation, append-only."""
        size = len(data)
        total = self.HEADER_SIZE + size
        
        if self.offset + total > self.BLOCK_SIZE:
            self.current_block += 1
            self.offset = 0
            if self.current_block >= len(self.blocks):
                return -1
        
        block = self.blocks[self.current_block]
        addr = self.offset
        
        # Pack header directly into memory
        struct.pack_into('dIIII', block, addr, timestamp, size, event_type, 0, 
                        self.head if self.head is not None else 0xFFFFFFFF)
        block[addr + self.HEADER_SIZE:addr + self.HEADER_SIZE + size] = data
        
        self.head = (self.current_block << 24) | addr
        self.offset += total
        return self.head
    
    def scan_window(self, start_ts: float, end_ts: float) -> list:
        """Linear scan, cache-friendly. Returns matching entries."""
        results = []
        ptr = self.head
        
        while ptr is not None and ptr != 0xFFFFFFFF:
            block_id = ptr >> 24
            offset = ptr & 0xFFFFFF
            block = self.blocks[block_id]
            
            ts, size, etype, flags, next_ptr = struct.unpack_from('dIIII', block, offset)
            if start_ts <= ts <= end_ts:
                data = bytes(block[offset + self.HEADER_SIZE:offset + self.HEADER_SIZE + size])
                results.append((ts, etype, data))
            
            ptr = next_ptr if next_ptr != 0xFFFFFFFF else None
            
        return results
    
    def compact(self):
        """Defrag by copying live data. Simple, brutal, effective."""
        self.current_block = 0
        self.offset = 0