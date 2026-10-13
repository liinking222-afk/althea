import mmap
import os
import struct
import fcntl
from pathlib import Path

class ModuleRegistry:
    HEADER_SIZE = 64
    ENTRY_SIZE = 256
    MAX_ENTRIES = 4096
    MAGIC = 0x414C5448  # 'ALTH'
    
    def __init__(self, path="/tmp/althea_modules.mmap"):
        self.path = path
        self.size = self.HEADER_SIZE + (self.ENTRY_SIZE * self.MAX_ENTRIES)
        
        if not os.path.exists(path):
            with open(path, 'wb') as f:
                f.write(b'\x00' * self.size)
        
        self.fd = os.open(path, os.O_RDWR)
        fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.mem = mmap.mmap(self.fd, self.size, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
        
        if self._read_u32(0) != self.MAGIC:
            self._write_u32(0, self.MAGIC)
            self._write_u32(4, 0)
    
    def _read_u32(self, offset):
        return struct.unpack('I', self.mem[offset:offset+4])[0]
    
    def _write_u32(self, offset, value):
        self.mem[offset:offset+4] = struct.pack('I', value)
    
    def register(self, module_name, version, status):
        count = self._read_u32(4)
        if count >= self.MAX_ENTRIES:
            return False
        
        offset = self.HEADER_SIZE + (count * self.ENTRY_SIZE)
        name_bytes = module_name.encode('utf-8')[:240]
        version_bytes = version.encode('utf-8')[:8]
        status_byte = status & 0xFF
        
        self.mem[offset:offset+240] = name_bytes.ljust(240, b'\x00')
        self.mem[offset+240:offset+248] = version_bytes.ljust(8, b'\x00')
        self.mem[offset+248] = status_byte
        
        self._write_u32(4, count + 1)
        self.mem.flush()
        return True
    
    def get_all(self):
        count = self._read_u32(4)
        modules = []
        for i in range(count):
            offset = self.HEADER_SIZE + (i * self.ENTRY_SIZE)
            name = self.mem[offset:offset+240].rstrip(b'\x00').decode('utf-8')
            version = self.mem[offset+240:offset+248].rstrip(b'\x00').decode('utf-8')
            status = self.mem[offset+248]
            if name:
                modules.append((name, version, status))
        return modules
    
    def close(self):
        self.mem.close()
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        os.close(self.fd)