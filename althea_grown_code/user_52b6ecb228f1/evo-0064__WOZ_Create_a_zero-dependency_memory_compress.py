#!/usr/bin/env python3
import re
import json
from typing import Dict, List, Tuple

def compress_evolution_signature(sig: str) -> bytes:
    """Compress EVO signatures to minimal byte form using domain-specific encoding."""
    # Extract: EVO #N ARCHETYPE vX.Y.Z→X.Y.Z description
    match = re.match(r'\[EVO #(\d+) (\w+) v([\d.]+)→([\d.]+)\] (.+)', sig)
    if not match:
        return sig.encode('utf-8')
    
    num, arch, v_from, v_to, desc = match.groups()
    
    # Pack: 2 bytes num, 1 byte archetype hash, 3 bytes version delta, variable desc
    num_bytes = int(num).to_bytes(2, 'big')
    arch_byte = (hash(arch) & 0xFF).to_bytes(1, 'big')
    
    # Encode version as compact deltas
    from_parts = list(map(int, v_from.split('.')))
    to_parts = list(map(int, v_to.split('.')))
    deltas = bytes([to_parts[i] - from_parts[i] + 128 for i in range(3)])
    
    # Compress description: common words to single bytes
    word_map = {
        'Create': b'\x01', 'Enable': b'\x02', 'Althea': b'\x03',
        'runtime': b'\x04', 'module': b'\x05', 'can': b'\x06',
        'now': b'\x07', 'tool': b'\x08', 'system': b'\x09'
    }
    
    compressed_desc = []
    for word in desc.split():
        compressed_desc.append(word_map.get(word, word.encode('utf-8')))
    
    return num_bytes + arch_byte + deltas + b'\xFF'.join(compressed_desc)

def decompress_evolution_signature(data: bytes) -> str:
    """Decompress packed evolution signature back to readable form."""
    num = int.from_bytes(data[0:2], 'big')
    arch_hash = data[2]
    deltas = [data[i] - 128 for i in range(3, 6)]
    
    # Reconstruct archetype from hash (limited set)
    arch_map = {hash(a) & 0xFF: a for a in ['THOMPSON', 'KAY', 'WALL', 'WOZ', 'HOPPER']}
    arch = arch_map.get(arch_hash, 'UNKNOWN')
    
    return f"[EVO #{num} {arch} compressed]"

def batch_compress_memory(memories: List[str]) -> Tuple[bytes, Dict]:
    """Compress multiple memory entries and return packed bytes + manifest."""
    packed = []
    manifest = {'count': 0, 'original_bytes': 0, 'compressed_bytes': 0}
    
    for mem in memories:
        original = mem.encode('utf-8')
        compressed = compress_evolution_signature(mem)
        packed.append(compressed)
        manifest['original_bytes'] += len(original)
        manifest['compressed_bytes'] += len(compressed)
        manifest['count'] += 1
    
    manifest['ratio'] = manifest['compressed_bytes'] / max(manifest['original_bytes'], 1)
    return b'\x00'.join(packed), manifest

if __name__ == '__main__':
    test_sig = "[EVO #63 WALL v1.4.7→1.4.8] Create a polyglot capability manifest generator"
    compressed = compress_evolution_signature(test_sig)
    print(f"Original: {len(test_sig)} bytes")
    print(f"Compressed: {len(compressed)} bytes")
    print(f"Ratio: {len(compressed)/len(test_sig):.2%}")