import re
from collections import defaultdict
from difflib import SequenceMatcher

def analyze_memory_redundancy(memory_entries: list[str]) -> dict:
    """
    Detects duplicate, near-duplicate, and fragmented memory patterns.
    Returns consolidation opportunities.
    """
    
    # Parse memory entries
    parsed = []
    for entry in memory_entries:
        match = re.match(r'\[(\w+)\s+([^\]]+)\]\s+(.+)', entry)
        if match:
            mem_type, identifier, content = match.groups()
            parsed.append({
                'type': mem_type,
                'id': identifier,
                'content': content,
                'raw': entry
            })
    
    # Detect exact duplicates
    exact_dupes = defaultdict(list)
    for i, mem in enumerate(parsed):
        exact_dupes[mem['raw']].append(i)
    
    # Detect near-duplicates (>0.85 similarity)
    near_dupes = []
    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            similarity = SequenceMatcher(
                None, 
                parsed[i]['content'], 
                parsed[j]['content']
            ).ratio()
            if similarity > 0.85:
                near_dupes.append((i, j, similarity))
    
    # Detect fragmented entries (same type/id pattern)
    fragments = defaultdict(list)
    for i, mem in enumerate(parsed):
        key = (mem['type'], mem['id'])
        fragments[key].append(i)
    
    return {
        'total_entries': len(memory_entries),
        'exact_duplicates': {k: v for k, v in exact_dupes.items() if len(v) > 1},
        'near_duplicates': near_dupes,
        'fragments': {k: v for k, v in fragments.items() if len(v) > 1},
        'consolidation_opportunity_count': (
            sum(len(v) - 1 for v in exact_dupes.values() if len(v) > 1) +
            len(near_dupes) +
            sum(len(v) - 1 for v in fragments.values() if len(v) > 1)
        )
    }

# Self-diagnostic on current memory state
if __name__ == '__main__':
    sample_memory = [
        "[SYSTEM-MAP] Althea subsystems and operator controls:",
        "[SYSTEM-MAP] Althea subsystems and operator controls:",
    ]
    result = analyze_memory_redundancy(sample_memory)
    print(f"Consolidation opportunities detected: {result['consolidation_opportunity_count']}")