#!/usr/bin/env python3
import struct
import zlib
from typing import NamedTuple, List, Optional

class Capability(NamedTuple):
    name: bytes
    lang: bytes
    invoke: bytes
    
class CapabilityRegistry:
    MAGIC = b'ALTH'
    VERSION = 1
    
    def __init__(self):
        self.caps: List[Capability] = []
    
    def register(self, name: str, lang: str, invoke: str):
        self.caps.append(Capability(
            name.encode('utf-8'),
            lang.encode('utf-8'),
            invoke.encode('utf-8')
        ))
    
    def serialize(self) -> bytes:
        buf = bytearray(self.MAGIC)
        buf.append(self.VERSION)
        buf.extend(struct.pack('<H', len(self.caps)))
        
        for cap in self.caps:
            for field in cap:
                buf.extend(struct.pack('<H', len(field)))
                buf.extend(field)
        
        return zlib.compress(bytes(buf), level=9)
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'CapabilityRegistry':
        buf = zlib.decompress(data)
        assert buf[:4] == cls.MAGIC
        assert buf[4] == cls.VERSION
        
        count = struct.unpack('<H', buf[5:7])[0]
        registry = cls()
        pos = 7
        
        for _ in range(count):
            fields = []
            for _ in range(3):
                length = struct.unpack('<H', buf[pos:pos+2])[0]
                pos += 2
                fields.append(buf[pos:pos+length])
                pos += length
            registry.caps.append(Capability(*fields))
        
        return registry
    
    def find(self, name: str) -> Optional[Capability]:
        name_bytes = name.encode('utf-8')
        for cap in self.caps:
            if cap.name == name_bytes:
                return cap
        return None
    
    def invoke_cmd(self, name: str) -> Optional[str]:
        cap = self.find(name)
        return cap.invoke.decode('utf-8') if cap else None

if __name__ == '__main__':
    reg = CapabilityRegistry()
    reg.register('market-inquiry', 'python', 'python3 modules/market_inquiry.py')
    reg.register('symmetry-breach', 'python', 'python3 modules/symmetry.py')
    data = reg.serialize()
    restored = CapabilityRegistry.deserialize(data)
    print(restored.invoke_cmd('market-inquiry'))