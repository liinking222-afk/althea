import sys
from typing import Any, Optional
from collections import defaultdict

class MemorySlab:
    """Zero-abstraction memory pool. Data structures over algorithms."""
    
    __slots__ = ('_pools', '_sizes', '_alloc_count', '_reuse_count')
    
    # Size classes: powers of 2 from 64B to 64KB
    SIZE_CLASSES = [64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]
    
    def __init__(self):
        self._pools: dict[int, list[bytearray]] = {sz: [] for sz in self.SIZE_CLASSES}
        self._sizes: dict[int, int] = {}  # object_id -> size_class
        self._alloc_count = 0
        self._reuse_count = 0
    
    def _size_class(self, size: int) -> int:
        """Find smallest size class >= size."""
        for sc in self.SIZE_CLASSES:
            if sc >= size:
                return sc
        return self.SIZE_CLASSES[-1]
    
    def alloc(self, size: int) -> bytearray:
        """Allocate or reuse a slab."""
        sc = self._size_class(size)
        pool = self._pools[sc]
        
        if pool:
            slab = pool.pop()
            self._reuse_count += 1
        else:
            slab = bytearray(sc)
            self._alloc_count += 1
        
        self._sizes[id(slab)] = sc
        return memoryview(slab)[:size]
    
    def free(self, slab: memoryview) -> None:
        """Return slab to pool."""
        obj_id = id(slab.obj)
        if obj_id not in self._sizes:
            return
        
        sc = self._sizes.pop(obj_id)
        # Zero the slab for security
        slab.obj[:] = b'\x00' * len(slab.obj)
        self._pools[sc].append(slab.obj)
    
    def stats(self) -> dict[str, Any]:
        """Performance metrics."""
        return {
            'alloc': self._alloc_count,
            'reuse': self._reuse_count,
            'reuse_rate': self._reuse_count / max(1, self._alloc_count + self._reuse_count),
            'pool_sizes': {sz: len(pool) for sz, pool in self._pools.items() if pool}
        }

# Global instance
SLAB = MemorySlab()