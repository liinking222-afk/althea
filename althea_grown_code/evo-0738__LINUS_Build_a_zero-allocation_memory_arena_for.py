import mmap
import struct
import os
from typing import Optional

class ModuleParamArena:
    """Zero-copy shared memory arena for inter-module parameter passing.
    Layout: [slot_count:4][slot_offsets:slot_count*4][data_region]
    Each slot: [type:1][size:4][payload:size]
    """
    
    SLOT_COUNT = 32
    HEADER_SIZE = 4 + (SLOT_COUNT * 4)
    ARENA_SIZE = 65536
    
    TYPE_INT = 0x01
    TYPE_FLOAT = 0x02
    TYPE_BYTES = 0x03
    
    def __init__(self, path: str = "/tmp/althea_arena"):
        self.path = path
        self.fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        os.ftruncate(self.fd, self.ARENA_SIZE)
        self.mem = mmap.mmap(self.fd, self.ARENA_SIZE, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
        self._init_header()
    
    def _init_header(self):
        struct.pack_into('<I', self.mem, 0, self.SLOT_COUNT)
        for i in range(self.SLOT_COUNT):
            struct.pack_into('<I', self.mem, 4 + i * 4, 0)
    
    def write_int(self, slot: int, value: int) -> bool:
        if slot >= self.SLOT_COUNT:
            return False
        offset = self._allocate_slot(slot, 5)
        if offset < 0:
            return False
        self.mem[offset] = self.TYPE_INT
        struct.pack_into('<i', self.mem, offset + 1, value)
        return True
    
    def write_float(self, slot: int, value: float) -> bool:
        if slot >= self.SLOT_COUNT:
            return False
        offset = self._allocate_slot(slot, 5)
        if offset < 0:
            return False
        self.mem[offset] = self.TYPE_FLOAT
        struct.pack_into('<f', self.mem, offset + 1, value)
        return True
    
    def write_bytes(self, slot: int, data: bytes) -> bool:
        if slot >= self.SLOT_COUNT or len(data) > 8192:
            return False
        offset = self._allocate_slot(slot, 5 + len(data))
        if offset < 0:
            return False
        self.mem[offset] = self.TYPE_BYTES
        struct.pack_into('<I', self.mem, offset + 1, len(data))
        self.mem[offset + 5:offset + 5 + len(data)] = data
        return True
    
    def read_int(self, slot: int) -> Optional[int]:
        offset = self._get_slot_offset(slot)
        if offset <= 0 or self.mem[offset] != self.TYPE_INT:
            return None
        return struct.unpack_from('<i', self.mem, offset + 1)[0]
    
    def read_float(self, slot: int) -> Optional[float]:
        offset = self._get_slot_offset(slot)
        if offset <= 0 or self.mem[offset] != self.TYPE_FLOAT:
            return None
        return struct.unpack_from('<f', self.mem, offset + 1)[0]
    
    def read_bytes(self, slot: int) -> Optional[bytes]:
        offset = self._get_slot_offset(slot)
        if offset <= 0 or self.mem[offset] != self.TYPE_BYTES:
            return None
        size = struct.unpack_from('<I', self.mem, offset + 1)[0]
        return bytes(self.mem[offset + 5:offset + 5 + size])
    
    def _allocate_slot(self, slot: int, size: int) -> int:
        offset = self.HEADER_SIZE + (slot * 256)
        struct.pack_into('<I', self.mem, 4 + slot * 4, offset)
        return offset
    
    def _get_slot_offset(self, slot: int) -> int:
        return struct.unpack_from('<I', self.mem, 4 + slot * 4)[0]
    
    def close(self):
        self.mem.close()
        os.close(self.fd)