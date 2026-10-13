import os
from collections import deque
from dataclasses import dataclass
from typing import Any, Optional

MEMORY_CAPACITY = int(os.getenv('ALTHEA_MEMORY_CAPACITY', '512'))

@dataclass
class MemoryEntry:
    __slots__ = ('timestamp', 'type', 'data', 'size')
    timestamp: float
    type: str
    data: Any
    size: int

class RingMemory:
    __slots__ = ('_buffer', '_capacity', '_total_bytes', '_max_bytes')
    
    def __init__(self, capacity: int = MEMORY_CAPACITY, max_bytes: int = 1_048_576):
        self._buffer = deque(maxlen=capacity)
        self._capacity = capacity
        self._total_bytes = 0
        self._max_bytes = max_bytes
    
    def push(self, entry: MemoryEntry) -> Optional[MemoryEntry]:
        evicted = None
        if len(self._buffer) == self._capacity:
            evicted = self._buffer[0]
            self._total_bytes -= evicted.size
        
        while self._total_bytes + entry.size > self._max_bytes and self._buffer:
            oldest = self._buffer.popleft()
            self._total_bytes -= oldest.size
            evicted = oldest
        
        self._buffer.append(entry)
        self._total_bytes += entry.size
        return evicted
    
    def get_recent(self, n: int) -> list[MemoryEntry]:
        if n >= len(self._buffer):
            return list(self._buffer)
        return list(self._buffer)[-n:]
    
    def scan(self, predicate) -> list[MemoryEntry]:
        return [e for e in self._buffer if predicate(e)]
    
    @property
    def count(self) -> int:
        return len(self._buffer)
    
    @property
    def bytes_used(self) -> int:
        return self._total_bytes
    
    def clear(self):
        self._buffer.clear()
        self._total_bytes = 0

_global_memory = RingMemory()

def memory() -> RingMemory:
    return _global_memory