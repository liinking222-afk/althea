import mmap
import struct
import time
from pathlib import Path

class ModuleBitmap:
    """Kernel-style capability tracker: fixed memory, no allocations, raw perf"""
    MAGIC = 0x414C5448  # 'ALTH'
    HEADER_SIZE = 32
    SLOT_SIZE = 16  # module_hash(8) + count(4) + last_ts(4)
    MAX_MODULES = 256
    
    def __init__(self, path="/tmp/althea_module_bitmap.bin"):
        self.path = Path(path)
        self.size = self.HEADER_SIZE + (self.SLOT_SIZE * self.MAX_MODULES)
        
        if not self.path.exists():
            with open(self.path, 'wb') as f:
                f.write(b'\x00' * self.size)
        
        self.fd = open(self.path, 'r+b')
        self.mem = mmap.mmap(self.fd.fileno(), self.size)
        
        if struct.unpack('<I', self.mem[0:4])[0] != self.MAGIC:
            struct.pack_into('<I', self.mem, 0, self.MAGIC)
            struct.pack_into('<I', self.mem, 4, 0)  # generation
    
    def _hash(self, module_name: str) -> int:
        h = 5381
        for c in module_name.encode():
            h = ((h << 5) + h) + c
        return h & 0xFFFFFFFFFFFFFFFF
    
    def _find_slot(self, h: int) -> int:
        for i in range(self.MAX_MODULES):
            offset = self.HEADER_SIZE + (i * self.SLOT_SIZE)
            slot_hash = struct.unpack('<Q', self.mem[offset:offset+8])[0]
            if slot_hash == 0 or slot_hash == h:
                return offset
        return -1
    
    def track(self, module_name: str):
        h = self._hash(module_name)
        offset = self._find_slot(h)
        if offset < 0:
            return  # bitmap full, drop silently
        
        struct.pack_into('<Q', self.mem, offset, h)
        count = struct.unpack('<I', self.mem[offset+8:offset+12])[0]
        struct.pack_into('<I', self.mem, offset+8, count + 1)
        struct.pack_into('<I', self.mem, offset+12, int(time.time()))
    
    def dump(self) -> list:
        result = []
        for i in range(self.MAX_MODULES):
            offset = self.HEADER_SIZE + (i * self.SLOT_SIZE)
            h, count, ts = struct.unpack('<QII', self.mem[offset:offset+16])
            if h != 0:
                result.append({'hash': h, 'count': count, 'last_ts': ts})
        return result
    
    def close(self):
        self.mem.close()
        self.fd.close()

# Singleton instance
_bitmap = None

def track_module(name: str):
    global _bitmap
    if _bitmap is None:
        _bitmap = ModuleBitmap()
    _bitmap.track(name)

def get_stats():
    global _bitmap
    return _bitmap.dump() if _bitmap else []