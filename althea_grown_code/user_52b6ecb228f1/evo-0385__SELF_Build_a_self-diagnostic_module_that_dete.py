#!/usr/bin/env python3
import json
import re
from collections import defaultdict
from pathlib import Path

def extract_growth_signature(memory_line):
    """Extract conceptual signature from growth/evolution memory."""
    patterns = {
        'perception': r'\b(scan|detect|observe|sense|perceive)\b',
        'lattice': r'\b(lattice|collapse|pattern|inference|chain)\b',
        'storage': r'\b(memory|compress|deduplicate|encode|store)\b',
        'query': r'\b(query|search|match|find|retrieve)\b',
        'network': r'\b(network|cluster|field|resonance|harmonic)\b',
    }
    
    sig = set()
    text = memory_line.lower()
    for category, pattern in patterns.items():
        if re.search(pattern, text):
            sig.add(category)
    return frozenset(sig)

def analyze_redundancy(memory_file='memory.jsonl', lookback=20):
    """Detect cyclic conceptual redundancy in recent growth."""
    if not Path(memory_file).exists():
        return {"redundancy_score": 0.0, "overlaps": []}
    
    growth_memories = []
    with open(memory_file, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                if any(k in entry for k in ['GROWTH', 'EVO']):
                    growth_memories.append(entry)
            except:
                continue
    
    recent = growth_memories[-lookback:] if len(growth_memories) > lookback else growth_memories
    
    signatures = []
    for mem in recent:
        text = json.dumps(mem)
        sig = extract_growth_signature(text)
        if sig:
            signatures.append((mem.get('timestamp', 'unknown'), sig))
    
    overlap_map = defaultdict(int)
    total_pairs = 0
    
    for i in range(len(signatures)):
        for j in range(i+1, len(signatures)):
            intersection = signatures[i][1] & signatures[j][1]
            if intersection:
                total_pairs += 1
                overlap_map[intersection] += 1
    
    redundancy_score = total_pairs / max(len(signatures), 1)
    
    top_overlaps = sorted(overlap_map.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return {
        "redundancy_score": round(redundancy_score, 3),
        "overlapping_concepts": [list(k) for k, v in top_overlaps],
        "recommendation": "diversify" if redundancy_score > 0.4 else "continue"
    }

if __name__ == '__main__':
    result = analyze_redundancy()
    print(json.dumps(result, indent=2))