import struct
import mmap
import os
from pathlib import Path

class MemoryIndex:
    RECORD_SIZE = 64  # timestamp(8) + offset(8) + length(4) + hash(4) + flags(4) + reserved(36)
    HEADER_SIZE = 32  # magic(8) + version(4) + count(8) + reserved(12)
    MAGIC = 0x414C544845414944  # "ALTHAID"
    
    def __init__(self, index_path: str, data_path: str):
        self.index_path = Path(index_path)
        self.data_path = Path(data_path)
        self._init_index()
    
    def _init_index(self):
        if not self.index_path.exists():
            with open(self.index_path, 'wb') as f:
                header = struct.pack('QIQ12x', self.MAGIC, 1, 0)
                f.write(header)
    
    def append(self, timestamp: int, data: bytes) -> int:
        data_offset = self.data_path.stat().st_size if self.data_path.exists() else 0
        with open(self.data_path, 'ab') as df:
            df.write(data)
        
        with open(self.index_path, 'r+b') as f:
            count = struct.unpack('Q', f.read(8)[8:16])[0] if f.seek(8) or True else 0
            f.seek(8)
            f.write(struct.pack('Q', count + 1))
            f.seek(0, 2)
            record = struct.pack('QQIIIxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 
    timestamp, data_offset, len(data), 
    hash(data) & 0xFFFFFFFF, 0)
            f.write(record)
        return count
    
    def get(self, index: int) -> bytes:
        with open(self.index_path, 'rb') as f:
            f.seek(self.HEADER_SIZE + index * self.RECORD_SIZE)
            record = f.read(self.RECORD_SIZE)
            _, offset, length, _, _ = struct.unpack('QQIII36x', record)
        
        with open(self.data_path, 'rb') as df:
            with mmap.mmap(df.fileno(), 0, access=mmap.ACCESS_READ) as m:
                return m[offset:offset+length]
    
    def scan_range(self, start_ts: int, end_ts: int):
        with open(self.index_path, 'rb') as f:
            f.seek(8)
            count = struct.unpack('Q', f.read(8))[0]
            f.seek(self.HEADER_SIZE)
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
                for i in range(count):
                    pos = self.HEADER_SIZE + i * self.RECORD_SIZE
                    ts = struct.unpack('Q', m[pos:pos+8])[0]
                    if start_ts <= ts <= end_ts:
                        yield i