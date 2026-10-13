#!/usr/bin/env python3
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

@dataclass
class Module:
    name: str
    version: str
    intent: str
    deps: Set[str]
    
    def signature(self) -> str:
        words = re.findall(r'\b\w{4,}\b', self.intent.lower())
        return ''.join(sorted(set(words)))[:32]

class MemoryCompactor:
    def __init__(self):
        self.modules: List[Module] = []
        self.sig_map: Dict[str, List[str]] = defaultdict(list)
        
    def ingest(self, name: str, version: str, intent: str, deps: str = ""):
        dep_set = set(d.strip() for d in deps.split(',') if d.strip())
        mod = Module(name, version, intent, dep_set)
        sig = mod.signature()
        
        self.sig_map[sig].append(name)
        self.modules.append(mod)
        
    def detect_collisions(self) -> List[Tuple[str, List[str]]]:
        return [(sig, names) for sig, names in self.sig_map.items() if len(names) > 1]
    
    def build_dag(self) -> Dict[str, Set[str]]:
        graph = {m.name: m.deps for m in self.modules}
        return graph
    
    def find_cycles(self) -> List[List[str]]:
        graph = self.build_dag()
        visiting = set()
        visited = set()
        cycles = []
        
        def dfs(node: str, path: List[str]):
            if node in visiting:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return
            if node in visited:
                return
            visiting.add(node)
            path.append(node)
            for dep in graph.get(node, []):
                if dep in graph:
                    dfs(dep, path[:])
            path.pop()
            visiting.remove(node)
            visited.add(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def compact(self) -> str:
        collisions = self.detect_collisions()
        cycles = self.find_cycles()
        graph = self.build_dag()
        
        report = f"MODULES={len(self.modules)} UNIQUE_SIGS={len(self.sig_map)}\n"
        if collisions:
            report += f"COLLISIONS={len(collisions)}\n"
            for sig, names in collisions[:3]:
                report += f"  {sig[:8]}: {','.join(names)}\n"
        if cycles:
            report += f"CYCLES={len(cycles)}\n"
        report += f"DEPS={sum(len(d) for d in graph.values())}\n"
        return report

if __name__ == "__main__":
    compactor = MemoryCompactor()
    print(compactor.compact())