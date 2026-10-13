import hashlib
import re
from typing import Dict, List, Set, Tuple

def semantic_fingerprint(memory_line: str) -> str:
    """Extract essence, ignore noise. Hash what matters."""
    # Strip timestamps, version numbers, instance IDs
    essence = re.sub(r'\d{4}(?:-\d{2}){2}T[\d:\.]+Z?', '', memory_line)
    essence = re.sub(r'v?\d+\.\d+\.\d+', '', essence)
    essence = re.sub(r'#\d+', '', essence)
    essence = re.sub(r'-\d{4}\]', ']', essence)
    essence = re.sub(r'/autonomous-\w+-\d+', '/autonomous-MODULE', essence)
    
    # Normalize whitespace
    essence = ' '.join(essence.split())
    
    # Hash the semantic core
    return hashlib.blake2b(essence.encode(), digest_size=16).hexdigest()

def find_duplicates(memory_lines: List[str]) -> Dict[str, List[int]]:
    """Group lines by semantic fingerprint."""
    fingerprints: Dict[str, List[int]] = {}
    
    for idx, line in enumerate(memory_lines):
        if not line.strip():
            continue
        fp = semantic_fingerprint(line)
        fingerprints.setdefault(fp, []).append(idx)
    
    return {fp: indices for fp, indices in fingerprints.items() if len(indices) > 1}

def compress_memory(memory_lines: List[str]) -> Tuple[List[str], int]:
    """Keep first instance, mark rest as collapsed."""
    duplicates = find_duplicates(memory_lines)
    keep_indices: Set[int] = set(range(len(memory_lines)))
    collapsed_count = 0
    
    for indices in duplicates.values():
        # Keep first, remove rest
        for idx in indices[1:]:
            keep_indices.discard(idx)
            collapsed_count += 1
    
    compressed = [memory_lines[i] for i in sorted(keep_indices)]
    return compressed, collapsed_count

def deduplicate_stream(input_text: str) -> str:
    """Main interface: deduplicate memory stream."""
    lines = input_text.split('\n')
    compressed, count = compress_memory(lines)
    result = '\n'.join(compressed)
    if count > 0:
        result += f"\n[DEDUP: collapsed {count} redundant memories]"
    return result