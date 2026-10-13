#!/usr/bin/env python3
import re
from pathlib import Path
from collections import defaultdict

class DepGraph:
    __slots__ = ('adj', 'refs', 'modules')
    
    def __init__(self):
        self.adj = defaultdict(list)
        self.refs = defaultdict(int)
        self.modules = set()
    
    def add_edge(self, src, dst):
        self.adj[src].append(dst)
        self.refs[dst] += 1
        self.modules.add(src)
        self.modules.add(dst)
    
    def cycles(self):
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.adj[node]:
                dfs(neighbor, path + [neighbor])
            
            rec_stack.remove(node)
        
        for mod in self.modules:
            if mod not in visited:
                dfs(mod, [mod])
        
        return cycles

def scan_module(path):
    import_re = re.compile(r'(?:from|import)\s+[\w.]+')
    with open(path) as f:
        return [m.split()[-1] for m in import_re.findall(f.read())]

def build_graph(root_dir):
    g = DepGraph()
    for py_file in Path(root_dir).rglob('*.py'):
        mod_name = str(py_file.stem)
        for dep in scan_module(py_file):
            if dep != mod_name:
                g.add_edge(mod_name, dep)
    return g

if __name__ == '__main__':
    import sys
    g = build_graph(sys.argv[1] if len(sys.argv) > 1 else '.')
    cycles = g.cycles()
    if cycles:
        print(f"CIRCULAR DEPS: {len(cycles)}")
        for c in cycles:
            print(" -> ".join(c))
    else:
        print("CLEAN: no cycles")