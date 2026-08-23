import re
from typing import Dict, List, Tuple
from collections import Counter
import hashlib

def extract_numerical_signature(text: str) -> Tuple[int, ...]:
    """Extract a compact numerical fingerprint from any text pattern."""
    numbers = re.findall(r'\d+', text)
    if not numbers:
        return (0, 0, 0, 0)
    
    nums = [int(n) for n in numbers[:10]]
    
    return (
        len(nums),
        sum(nums) % 10000,
        max(nums) if nums else 0,
        int(hashlib.md5(text.encode()).hexdigest()[:4], 16)
    )

def compress_memory_block(memories: List[str]) -> Dict[Tuple[int, ...], List[int]]:
    """Compress memory logs into signature clusters for O(1) similarity lookup."""
    sig_map = {}
    for idx, mem in enumerate(memories):
        sig = extract_numerical_signature(mem)
        if sig not in sig_map:
            sig_map[sig] = []
        sig_map[sig].append(idx)
    return sig_map

def find_similar_memories(target: str, sig_map: Dict[Tuple[int, ...], List[int]], 
                          memories: List[str]) -> List[str]:
    """Retrieve similar memory patterns using signature matching."""
    target_sig = extract_numerical_signature(target)
    
    if target_sig in sig_map:
        return [memories[i] for i in sig_map[target_sig]]
    
    close_sigs = sorted(sig_map.keys(), 
                       key=lambda s: sum(abs(a-b) for a, b in zip(s, target_sig)))[:3]
    
    result_indices = []
    for sig in close_sigs:
        result_indices.extend(sig_map[sig])
    
    return [memories[i] for i in result_indices[:5]]

def signature_distance(sig1: Tuple[int, ...], sig2: Tuple[int, ...]) -> int:
    """Manhattan distance between two signatures for clustering."""
    return sum(abs(a - b) for a, b in zip(sig1, sig2))