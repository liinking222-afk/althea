#!/usr/bin/env python3
"""
/autonomous-binary-introspection-9201
Minimal binary file structure analyzer - extract maximum insight with minimum memory.
Woz principle: every byte read must yield actionable intelligence.
"""
import sys
import struct
from pathlib import Path

MAGIC_SIGS = {
    b'\x89PNG': 'PNG', b'GIF8': 'GIF', b'\xff\xd8\xff': 'JPEG',
    b'%PDF': 'PDF', b'PK\x03\x04': 'ZIP/DOCX/JAR',
    b'\x1f\x8b': 'GZIP', b'BM': 'BMP', b'RIFF': 'RIFF/WAV/AVI',
    b'\x00\x00\x01\xba': 'MPEG', b'\x00\x00\x01\xb3': 'MPEG',
    b'ftyp': 'MP4/MOV', b'\x7fELF': 'ELF', b'MZ': 'EXE/DLL',
    b'\xca\xfe\xba\xbe': 'MACH-O', b'\xfe\xed\xfa': 'MACH-O'
}

def introspect(filepath, sample_size=8192):
    """Extract structural fingerprint with minimal I/O."""
    p = Path(filepath)
    size = p.stat().st_size
    
    with open(filepath, 'rb') as f:
        header = f.read(min(sample_size, size))
        
        # Magic signature detection
        fmt = 'UNKNOWN'
        for sig, name in MAGIC_SIGS.items():
            if header.startswith(sig) or sig in header[:64]:
                fmt = name
                break
        
        # Entropy approximation (byte distribution)
        if len(header) >= 256:
            counts = [0] * 256
            for b in header[:256]:
                counts[b] += 1
            non_zero = sum(1 for c in counts if c > 0)
            entropy_proxy = non_zero / 256.0
        else:
            entropy_proxy = 0.0
        
        # Structural markers
        null_density = header.count(b'\x00') / len(header) if header else 0
        ascii_density = sum(1 for b in header if 32 <= b < 127) / len(header) if header else 0
        
        # Seek to end for footer analysis (if large file)
        footer = b''
        if size > sample_size * 2:
            f.seek(-min(512, size), 2)
            footer = f.read(512)
    
    return {
        'format': fmt,
        'size': size,
        'entropy_proxy': round(entropy_proxy, 3),
        'null_density': round(null_density, 3),
        'ascii_density': round(ascii_density, 3),
        'has_footer_sig': bool(footer and any(sig in footer for sig in MAGIC_SIGS.keys())),
        'likely_structured': entropy_proxy > 0.4 and null_density < 0.5
    }

if __name__ == '__main__':
    import json
    result = introspect(sys.argv[1]) if len(sys.argv) > 1 else {'error': 'no file'}
    print(json.dumps(result, indent=2))