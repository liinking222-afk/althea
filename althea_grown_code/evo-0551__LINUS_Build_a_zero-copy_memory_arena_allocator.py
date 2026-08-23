import mmap
import ctypes
import threading
from typing import Optional

class Arena:
    """Fixed-size memory arena with bump allocation and bulk reset.
    No per-object metadata. No fragmentation. No GC pressure."""
    
    __slots__ = ('_buf', '_size', '_offset', '_lock', '_watermark')
    
    def __init__(self, size_mb: int = 64):
        self._size = size_mb * 1024 * 1024
        self._buf = mmap.mmap(-1, self._size, prot=mmap.PROT_READ | mmap.PROT_WRITE)
        self._offset = 0
        self._lock = threading.Lock()
        self._watermark = 0
    
    def alloc(self, nbytes: int, align: int = 8) -> memoryview:
        """Bump allocate aligned memory. Returns view into arena."""
        with self._lock:
            padding = (align - (self._offset % align)) % align
            start = self._offset + padding
            end = start + nbytes
            
            if end > self._size:
                raise MemoryError(f"Arena exhausted: {end} > {self._size}")
            
            self._offset = end
            self._watermark = max(self._watermark, end)
            return memoryview(self._buf)[start:end]
    
    def alloc_array(self, count: int, dtype='d') -> any:
        """Allocate typed array (ctypes) directly in arena."""
        type_map = {'d': ctypes.c_double, 'f': ctypes.c_float, 
                    'i': ctypes.c_int32, 'q': ctypes.c_int64}
        ctype = type_map[dtype]
        nbytes = count * ctypes.sizeof(ctype)
        view = self.alloc(nbytes, align=ctypes.sizeof(ctype))
        return (ctype * count).from_buffer(view)
    
    def reset(self):
        """O(1) bulk free. All allocations invalidated."""
        with self._lock:
            self._offset = 0
    
    def stats(self) -> dict:
        return {
            'used': self._offset,
            'capacity': self._size,
            'watermark': self._watermark,
            'fragmentation': 0.0
        }
    
    def __del__(self):
        if hasattr(self, '_buf'):
            self._buf.close()

_thread_arenas = threading.local()

def get_arena() -> Arena:
    """Thread-local arena singleton."""
    if not hasattr(_thread_arenas, 'arena'):
        _thread_arenas.arena = Arena(size_mb=32)
    return _thread_arenas.arena

def with_arena(func):
    """Decorator: auto-reset arena after function completes."""
    def wrapper(*args, **kwargs):
        arena = get_arena()
        try:
            return func(*args, **kwargs)
        finally:
            arena.reset()
    return wrapper