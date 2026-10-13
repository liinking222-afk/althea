#!/usr/bin/env python3
"""Module Dependency Graph Analyzer - Detects cycles and orphans in Althea's lattice"""

import re
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

def parse_module_dependencies(module_code: str) -> Set[str]:
    """Extract module dependencies from import statements and function calls"""
    deps = set()
    # Python imports
    deps.update(re.findall(r'from\s+(\w+)\s+import', module_code))
    deps.update(re.findall(r'import\s+(\w+)', module_code))
    # Explicit module calls (common pattern: module_name.function())
    deps.update(re.findall(r'(\w+)\.[\w_]+\(', module_code))
    return deps

def build_dependency_graph(modules: Dict[str, str]) -> Dict[str, Set[str]]:
    """Build adjacency list of module dependencies"""
    graph = defaultdict(set)
    for module_name, code in modules.items():
        deps = parse_module_dependencies(code)
        # Filter to only known modules
        graph[module_name] = deps & modules.keys()
    return graph

def detect_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Detect all cycles using DFS with path tracking"""
    cycles = []
    visited = set()
    rec_stack = set()
    path = []
    
    def dfs(node: str):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
        
        path.pop()
        rec_stack.remove(node)
    
    for node in graph:
        if node not in visited:
            dfs(node)
    
    return cycles

def find_orphans(graph: Dict[str, Set[str]], modules: Set[str]) -> Set[str]:
    """Find modules that are never imported by others"""
    referenced = set()
    for deps in graph.values():
        referenced.update(deps)
    return modules - referenced - {'main', '__main__', 'core', 'bootstrap'}

def analyze_lattice(modules: Dict[str, str]) -> Dict[str, any]:
    """Full lattice health analysis"""
    graph = build_dependency_graph(modules)
    cycles = detect_cycles(graph)
    orphans = find_orphans(graph, set(modules.keys()))
    
    return {
        'graph': dict(graph),
        'cycles': cycles,
        'orphans': list(orphans),
        'health_score': 100 - (len(cycles) * 20 + len(orphans) * 2)
    }