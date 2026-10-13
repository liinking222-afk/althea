#!/usr/bin/env python3
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def extract_memory_refs(memory_line: str) -> Tuple[str, Set[str]]:
    """Extract module ID and referenced modules from memory line."""
    module_id = ""
    refs = set()
    
    # Extract module identifier (EVO version or GROWTH path)
    evo_match = re.search(r'\[EVO #\d+ (\w+) v[\d.]+→[\d.]+\]', memory_line)
    growth_match = re.search(r'\[GROWTH (/[\w-]+)\]', memory_line)
    
    if evo_match:
        module_id = f"EVO:{evo_match.group(1)}"
    elif growth_match:
        module_id = f"GROWTH:{growth_match.group(1)}"
    
    # Extract cross-references to other modules
    for match in re.finditer(r'\b(CARMACK|KERNIGHAN|KNUTH|rationale|perception|memory)\b', memory_line, re.IGNORECASE):
        ref = match.group(1).upper()
        if ref in ['RATIONALE', 'PERCEPTION', 'MEMORY']:
            refs.add(f"GROWTH:{ref}")
        else:
            refs.add(f"EVO:{ref}")
    
    return module_id, refs

def analyze_coherence(memories: List[str]) -> Dict[str, any]:
    """Analyze lattice coherence and identify orphaned modules."""
    graph = defaultdict(set)
    all_modules = set()
    
    for line in memories:
        mod_id, refs = extract_memory_refs(line)
        if mod_id:
            all_modules.add(mod_id)
            graph[mod_id] = refs
    
    # Find orphaned modules (no incoming or outgoing edges)
    orphaned = []
    weakly_connected = []
    
    for mod in all_modules:
        outgoing = len(graph[mod])
        incoming = sum(1 for other_refs in graph.values() if mod in other_refs)
        
        if outgoing == 0 and incoming == 0:
            orphaned.append(mod)
        elif outgoing + incoming == 1:
            weakly_connected.append((mod, outgoing, incoming))
    
    return {
        'orphaned': orphaned,
        'weakly_connected': weakly_connected,
        'graph': dict(graph),
        'total_modules': len(all_modules)
    }

def synthesize_bridge_suggestions(analysis: Dict) -> List[str]:
    """Generate suggestions for bridging isolated modules."""
    suggestions = []
    
    for orphan in analysis['orphaned']:
        suggestions.append(f"BRIDGE_NEEDED: {orphan} has zero lattice connections")
    
    for mod, out, inc in analysis['weakly_connected']:
        if out == 0:
            suggestions.append(f"OUTPUT_NEEDED: {mod} consumes but never produces")
        if inc == 0:
            suggestions.append(f"INPUT_NEEDED: {mod} produces but never consumed")
    
    return suggestions

if __name__ == "__main__":
    import sys
    memories = [line.strip() for line in sys.stdin if line.strip()]
    analysis = analyze_coherence(memories)
    bridges = synthesize_bridge_suggestions(analysis)
    
    print(f"COHERENCE: {len(analysis['orphaned'])} orphaned, {len(analysis['weakly_connected'])} weak")
    for bridge in bridges:
        print(bridge)