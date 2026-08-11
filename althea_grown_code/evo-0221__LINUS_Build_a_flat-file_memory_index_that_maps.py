#!/usr/bin/env python3
import re
from collections import defaultdict
from dataclasses import dataclass

@dataclass
class MemoryNode:
    id: str
    type: str  # EVO, GROWTH
    content: str
    deps: list  # direct structural dependencies

class FlatMemoryIndex:
    def __init__(self):
        self.nodes = {}  # id -> MemoryNode
        self.type_idx = defaultdict(list)  # type -> [ids]
        self.dep_graph = defaultdict(set)  # id -> {dependent_ids}
        
    def add(self, raw_memory: str):
        if match := re.match(r'\[(\w+)\s+([^\]]+)\]\s+(.+)', raw_memory):
            mtype, mid, content = match.groups()
            node = MemoryNode(mid.strip(), mtype, content.strip(), [])
            
            # Extract structural deps from content
            deps = re.findall(r'(?:seam|gap|integrate|compose|depend|chain|link)\w*\s+(\w+)', content.lower())
            node.deps = list(set(deps))
            
            self.nodes[node.id] = node
            self.type_idx[node.type].append(node.id)
            
            for dep in node.deps:
                self.dep_graph[dep].add(node.id)
    
    def scan_seams(self):
        """Find capability gaps: EVO nodes with no dependent GROWTH"""
        seams = []
        for evo_id in self.type_idx['EVO']:
            if not any(g for g in self.type_idx['GROWTH'] 
                      if evo_id in self.nodes[g].deps or 
                      self.nodes[evo_id].id in self.dep_graph.get(self.nodes[g].id, set())):
                seams.append(self.nodes[evo_id])
        return seams
    
    def hot_capabilities(self):
        """Most depended-upon nodes"""
        counts = defaultdict(int)
        for deps in self.dep_graph.values():
            for d in deps:
                counts[d] += 1
        return sorted(counts.items(), key=lambda x: -x[1])[:5]
    
    def dump_graph(self):
        for nid, node in self.nodes.items():
            deps = ','.join(node.deps) if node.deps else 'ROOT'
            print(f"{node.type}:{nid} -> [{deps}]")

if __name__ == '__main__':
    idx = FlatMemoryIndex()
    memories = [
        "[GROWTH /autonomous-syntactic-phase-shift] Syntactic Phase Shift",
        "[EVO #220 SELF v1.17.10→1.18.0] Build seam detector",
        "[GROWTH /autonomous-superposition-collapse-547a] Superposition Collapse",
    ]
    for m in memories:
        idx.add(m)
    seams = idx.scan_seams()
    print(f"SEAMS: {len(seams)}")