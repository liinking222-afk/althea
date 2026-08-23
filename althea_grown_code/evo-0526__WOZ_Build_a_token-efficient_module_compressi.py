#!/usr/bin/env python3
import json
import zlib
import base64
from typing import Dict, Any, List

def compress_module(module: Dict[str, Any]) -> str:
    """Compress module definition to minimal representation."""
    core = {
        'n': module.get('name', ''),
        't': module.get('type', ''),
        'v': module.get('version', ''),
        'c': module.get('code_hash', '')[:8],  # 8 chars sufficient
    }
    
    # Optional fields only if present
    if 'deps' in module:
        core['d'] = module['deps']
    if 'tags' in module:
        core['g'] = module['tags'][:3]  # max 3 tags
    
    packed = json.dumps(core, separators=(',', ':'))
    compressed = zlib.compress(packed.encode(), level=9)
    return base64.b85encode(compressed).decode()

def decompress_module(compressed: str) -> Dict[str, Any]:
    """Decompress module back to usable form."""
    decoded = base64.b85decode(compressed.encode())
    decompressed = zlib.decompress(decoded)
    core = json.loads(decompressed)
    
    return {
        'name': core['n'],
        'type': core['t'],
        'version': core['v'],
        'code_hash': core['c'],
        'deps': core.get('d', []),
        'tags': core.get('g', [])
    }

def pack_registry(modules: List[Dict[str, Any]]) -> str:
    """Pack entire registry into compressed stream."""
    compressed = [compress_module(m) for m in modules]
    return '\n'.join(compressed)

def unpack_registry(packed: str) -> List[Dict[str, Any]]:
    """Unpack compressed registry stream."""
    lines = packed.strip().split('\n')
    return [decompress_module(line) for line in lines if line]

def compression_ratio(original: str, compressed: str) -> float:
    """Calculate space savings."""
    return 1 - (len(compressed) / len(original))

if __name__ == '__main__':
    test_mod = {
        'name': '/autonomous-test-module',
        'type': 'AUTOSYNTH',
        'version': '1.0.0',
        'code_hash': 'a1b2c3d4e5f6g7h8',
        'tags': ['test', 'demo', 'compression', 'extra']
    }
    
    compressed = compress_module(test_mod)
    restored = decompress_module(compressed)
    
    orig_size = len(json.dumps(test_mod))
    comp_size = len(compressed)
    print(f"Compression: {orig_size}→{comp_size} bytes ({compression_ratio(json.dumps(test_mod), compressed)*100:.1f}% saved)")