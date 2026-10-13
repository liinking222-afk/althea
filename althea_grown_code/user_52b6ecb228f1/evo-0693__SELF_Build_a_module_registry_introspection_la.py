import re
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple

def analyze_module_connectivity(memory_log: List[str]) -> Dict:
    """Introspect Althea's module graph for structural weaknesses."""
    
    modules = {}
    invocations = defaultdict(int)
    co_occurrence = defaultdict(lambda: defaultdict(int))
    tags = defaultdict(set)
    
    # Parse memory entries
    for entry in memory_log:
        # Extract module identifiers
        if match := re.search(r'\[(AUTOSYNTH|GROWTH|EVO)\s+([/\w\-]+)', entry):
            mod_type, mod_id = match.groups()
            modules[mod_id] = {'type': mod_type, 'raw': entry}
            
            # Extract capability tags
            if '(' in entry and ')' in entry:
                tag_match = re.search(r'\(([^)]+)\)', entry)
                if tag_match:
                    tags[mod_id].add(tag_match.group(1))
    
    # Detect synthesis opportunities
    tag_frequency = Counter()
    for mod_tags in tags.values():
        tag_frequency.update(mod_tags)
    
    # Find orphaned modules (single-tag, rare category)
    orphans = []
    for mod_id, mod_tags in tags.items():
        if len(mod_tags) == 1:
            tag = list(mod_tags)[0]
            if tag_frequency[tag] == 1:
                orphans.append(mod_id)
    
    # Find overloaded categories
    overloaded = {tag: count for tag, count in tag_frequency.items() if count >= 3}
    
    # Detect missing bridges (tags that never co-occur)
    all_tags = set(tag_frequency.keys())
    bridge_gaps = []
    tag_list = list(all_tags)
    for i, tag1 in enumerate(tag_list):
        for tag2 in tag_list[i+1:]:
            # Check if any module has both tags
            bridged = any(tag1 in mod_tags and tag2 in mod_tags 
                         for mod_tags in tags.values())
            if not bridged and tag_frequency[tag1] > 1 and tag_frequency[tag2] > 1:
                bridge_gaps.append((tag1, tag2))
    
    return {
        'total_modules': len(modules),
        'orphaned_modules': orphans,
        'overloaded_categories': overloaded,
        'bridge_gaps': bridge_gaps[:5],  # Top 5 missing connections
        'synthesis_priority': max(overloaded.items(), key=lambda x: x[1])[0] if overloaded else None
    }

# Self-diagnostic checkpoint
def introspect():
    """Entry point for module connectivity analysis."""
    return analyze_module_connectivity