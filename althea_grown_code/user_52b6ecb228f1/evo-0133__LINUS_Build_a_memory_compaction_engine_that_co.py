#!/usr/bin/env python3
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set

@dataclass
class EvolutionKernel:
    concept: str
    instances: List[str]
    frequency: int
    archetypes: Set[str]
    
def extract_concept_kernel(intent: str) -> str:
    """Strip noise words, extract semantic core."""
    noise = {'build', 'a', 'an', 'the', 'that', 'which', 'with', 'for', 'to', 'of', 'and'}
    words = re.findall(r'\b[a-z]{3,}\b', intent.lower())
    core = [w for w in words if w not in noise]
    return ' '.join(sorted(set(core))[:3])

def compact_memory_log(log_entries: List[str]) -> Dict[str, EvolutionKernel]:
    """Monolithic compaction: O(n) single pass, hash-based dedup."""
    kernels = defaultdict(lambda: {'instances': [], 'archetypes': set(), 'freq': 0})
    
    for entry in log_entries:
        evo_match = re.search(r'\[EVO #(\d+) (\w+) v[\d.]+\] (.+?) —', entry)
        if not evo_match:
            continue
        
        evo_num, archetype, intent = evo_match.groups()
        kernel_id = extract_concept_kernel(intent)
        
        kernels[kernel_id]['instances'].append(f"#{evo_num}")
        kernels[kernel_id]['archetypes'].add(archetype)
        kernels[kernel_id]['freq'] += 1
    
    return {
        k: EvolutionKernel(
            concept=k,
            instances=v['instances'],
            frequency=v['freq'],
            archetypes=v['archetypes']
        )
        for k, v in kernels.items() if v['freq'] > 1
    }

def get_consolidation_targets(kernels: Dict[str, EvolutionKernel]) -> List[str]:
    """Return kernel IDs where frequency indicates redundancy."""
    return sorted(
        [k for k, v in kernels.items() if v.frequency >= 3],
        key=lambda k: kernels[k].frequency,
        reverse=True
    )

if __name__ == '__main__':
    test_log = [
        "[EVO #132 SELF v1.9.10→1.10.0] Build a meta-evolution analyzer that detects when recent growth modules share semantic overlap",
        "[EVO #131 BACKUS v1.9.9→1.9.10] Build a pure functional combinator library that treats cognitive operations",
        "[EVO #130 WOZ v1.9.8→1.9.9] Build a lightweight dependency tracker that monitors which cognitive modules"
    ]
    
    kernels = compact_memory_log(test_log)
    targets = get_consolidation_targets(kernels)
    
    for kid in targets:
        k = kernels[kid]
        print(f"{k.concept}: {k.frequency}× {k.instances} [{','.join(k.archetypes)}]")