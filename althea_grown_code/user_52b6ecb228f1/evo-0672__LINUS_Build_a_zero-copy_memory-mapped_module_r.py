import mmap
import struct
import hashlib
import os
from pathlib import Path

class ModuleRegistry:
    MAGIC = 0x414C5448  # 'ALTH'
    HEADER_FMT = '<IIQ'  # magic, count, timestamp
    ENTRY_FMT = '<32sQ32s'  # hash, offset, name_hash
    ENTRY_SIZE = struct.calcsize(ENTRY_FMT)
    MAX_ENTRIES = 4096
    
    def __init__(self, path='/tmp/althea_modules.bin'):
        self.path = Path(path)
        self.size = 4096 + (self.MAX_ENTRIES * self.ENTRY_SIZE)
        self._init_file()
        self.fd = os.open(self.path, os.O_RDWR)
        self.mem = mmap.mmap(self.fd, self.size, access=mmap.ACCESS_WRITE)
        
    def _init_file(self):
        if not self.path.exists():
            with open(self.path, 'wb') as f:
                header = struct.pack(self.HEADER_FMT, self.MAGIC, 0, 0)
                f.write(header + b'\x00' * (self.size - len(header)))
    
    def _hash(self, name: str) -> bytes:
        return hashlib.blake2b(name.encode(), digest_size=32).digest()
    
    def register(self, name: str, offset: int) -> bool:
        name_hash = self._hash(name)
        self.mem.seek(0)
        magic, count, ts = struct.unpack(self.HEADER_FMT, self.mem.read(12))
        
        if count >= self.MAX_ENTRIES:
            return False
            
        entry_pos = 4096 + (count * self.ENTRY_SIZE)
        self.mem.seek(entry_pos)
        self.mem.write(struct.pack(self.ENTRY_FMT, name_hash, offset, name_hash))
        
        self.mem.seek(0)
        self.mem.write(struct.pack(self.HEADER_FMT, self.MAGIC, count + 1, ts + 1))
        self.mem.flush()
        return True
    
    def lookup(self, name: str) -> int:
        target = self._hash(name)
        self.mem.seek(0)
        _, count, _ = struct.unpack(self.HEADER_FMT, self.mem.read(12))
        
        self.mem.seek(4096)
        entries = self.mem.read(count * self.ENTRY_SIZE)
        
        for i in range(count):
            offset = i * self.ENTRY_SIZE
            entry = entries[offset:offset + self.ENTRY_SIZE]
            h, off, _ = struct.unpack(self.ENTRY_FMT, entry)
            if h == target:
                return off
        return -1
    
    def __del__(self):
        if hasattr(self, 'mem'):
            self.mem.close()
        if hasattr(self, 'fd'):
            os.close(self.fd)

registry = ModuleRegistry()