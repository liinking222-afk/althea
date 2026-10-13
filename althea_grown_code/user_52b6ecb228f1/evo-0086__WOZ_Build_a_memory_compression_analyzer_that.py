#!/usr/bin/env python3
import re
from collections import defaultdict
from typing import List, Dict, Tuple

def parse_memory_line(line: str) -> Dict:
    """Extract structured data from memory line."""
    pattern = r'memory_count=(\d+).*?\((\d+) bytes\)'
    match = re.search(pattern, line)
    if match:
        return {
            'count': int(match.group(1)),
            'bytes': int(match.group(2)),
            'raw': line
        }
    return None

def compute_entropy_score(memories: List[Dict]) -> float:
    """Calculate information density metric."""
    if not memories:
        return 0.0
    byte_deltas = []
    for i in range(len(memories) - 1):
        delta = abs(memories[i]['bytes'] - memories[i+1]['bytes'])
        byte_deltas.append(delta)
    
    avg_delta = sum(byte_deltas) / len(byte_deltas) if byte_deltas else 0
    total_bytes = sum(m['bytes'] for m in memories)
    avg_bytes = total_bytes / len(memories)
    
    return (avg_delta / avg_bytes) if avg_bytes > 0 else 0.0

def find_optimal_subset(memories: List[Dict], target_ratio: float = 0.4) -> List[int]:
    """Select minimal memory set preserving maximum variance."""
    if not memories:
        return []
    
    target_size = max(2, int(len(memories) * target_ratio))
    indices = [0]  # Always keep first
    
    byte_values = [m['bytes'] for m in memories]
    remaining = set(range(1, len(memories)))
    
    while len(indices) < target_size and remaining:
        max_variance = -1
        best_idx = None
        
        for idx in remaining:
            test_set = sorted(indices + [idx])
            variance = sum((byte_values[i] - byte_values[test_set[j]]) ** 2 
                          for j, i in enumerate(test_set[:-1]))
            if variance > max_variance:
                max_variance = variance
                best_idx = idx
        
        if best_idx:
            indices.append(best_idx)
            remaining.remove(best_idx)
    
    return sorted(indices)

def analyze_memory_stream(memory_lines: List[str]) -> Dict:
    """Main compression analysis."""
    memories = [parse_memory_line(line) for line in memory_lines]
    memories = [m for m in memories if m]
    
    entropy = compute_entropy_score(memories)
    optimal_indices = find_optimal_subset(memories)
    compression_ratio = len(optimal_indices) / len(memories) if memories else 0
    
    return {
        'total_memories': len(memories),
        'entropy_score': entropy,
        'optimal_subset_size': len(optimal_indices),
        'compression_ratio': compression_ratio,
        'keep_indices': optimal_indices
    }

if __name__ == '__main__':
    sample = [
        "[SELF-VISION] memory_count=512 (18607 bytes)",
        "[SELF-VISION] memory_count=511 (18685 bytes)",
        "[SELF-VISION] memory_count=510 (19861 bytes)",
        "[SELF-VISION] memory_count=509 (18553 bytes)",
        "[SELF-VISION] memory_count=508 (20071 bytes)",
        "[SELF-VISION] memory_count=507 (18202 bytes)",
        "[SELF-VISION] memory_count=506 (18505 bytes)",
    ]
    result = analyze_memory_stream(sample)
    print(f"COMPRESSION: {result['compression_ratio']:.1%} | ENTROPY: {result['entropy_score']:.4f}")
    print(f"KEEP: {result['keep_indices']}")