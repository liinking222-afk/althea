import mmap
import struct
import os
from pathlib import Path

class TraceLog:
    MAGIC = 0x414C5448  # 'ALTH'
    HEADER_SIZE = 32
    ENTRY_SIZE = 256
    
    def __init__(self, path="/tmp/althea_trace.log", capacity=4096):
        self.path = Path(path)
        self.capacity = capacity
        self.size = self.HEADER_SIZE + (self.ENTRY_SIZE * capacity)
        
        if not self.path.exists():
            with open(self.path, 'wb') as f:
                f.write(b'\x00' * self.size)
        
        self.fd = os.open(self.path, os.O_RDWR)
        self.mem = mmap.mmap(self.fd, self.size)
        
        if struct.unpack('I', self.mem[:4])[0] != self.MAGIC:
            struct.pack_into('IQQQ', self.mem, 0, self.MAGIC, 0, 0, 0)
    
    def _offset(self, idx):
        return self.HEADER_SIZE + (idx % self.capacity) * self.ENTRY_SIZE
    
    def append(self, event_type, data):
        head = struct.unpack('Q', self.mem[8:16])[0]
        offset = self._offset(head)
        
        payload = data.encode('utf-8')[:240]
        struct.pack_into('HH', self.mem, offset, event_type, len(payload))
        self.mem[offset+4:offset+4+len(payload)] = payload
        
        struct.pack_into('Q', self.mem, 8, head + 1)
        self.mem.flush()
    
    def scan_residual(self):
        head = struct.unpack('Q', self.mem[8:16])[0]
        residuals = []
        
        for i in range(min(head, self.capacity)):
            offset = self._offset(head - i - 1)
            etype, dlen = struct.unpack('HH', self.mem[offset:offset+4])
            if etype > 0:
                data = self.mem[offset+4:offset+4+dlen].decode('utf-8', errors='ignore')
                residuals.append((etype, data))
        
        return residuals
    
    def close(self):
        self.mem.close()
        os.close(self.fd)

log = TraceLog()
log.append(1, "GROWTH_autonomous-trace-spectrality")
log.append(2, "CODE-GEN_eval_direct")
print(f"Residuals: {len(log.scan_residual())}")