#!/usr/bin/env python3
"""Module Dependency Graph Analyzer - Maps functional relationships between autonomous modules."""

import re
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple

def parse_module_signature(module_path: str) -> Dict:
    """Extract imports, exports, and function calls from module code."""
    try:
        with open(module_path, 'r') as f:
            content = f.read()
    except:
        return {"imports": set(), "exports": set(), "calls": set()}
    
    imports = set(re.findall(r'(?:from|import)\s+([a-zA-Z0-9_.-]+)', content))
    exports = set(re.findall(r'def\s+([a-zA-Z0-9_]+)\s*\(', content))
    calls = set(re.findall(r'([a-zA-Z0-9_]+)\s*\(', content)) - exports
    
    return {"imports": imports, "exports": exports, "calls": calls}

def build_dependency_graph(module_list: List[str]) -> Dict[str, Set[str]]:
    """Construct directed graph of module dependencies."""
    graph = defaultdict(set)
    module_data = {}
    
    for module in module_list:
        module_data[module] = parse_module_signature(module)
    
    for mod_a in module_list:
        for mod_b in module_list:
            if mod_a == mod_b:
                continue
            # If mod_a imports or calls anything exported by mod_b
            if module_data[mod_a]["imports"] & {mod_b.split('/')[-1].replace('.py', '')}:
                graph[mod_a].add(mod_b)
            if module_data[mod_a]["calls"] & module_data[mod_b]["exports"]:
                graph[mod_a].add(mod_b)
    
    return graph

def find_orphans(graph: Dict[str, Set[str]], all_modules: Set[str]) -> Set[str]:
    """Identify modules with no incoming or outgoing edges."""
    has_incoming = set()
    has_outgoing = set(graph.keys())
    
    for deps in graph.values():
        has_incoming.update(deps)
    
    connected = has_incoming | has_outgoing
    return all_modules - connected

def find_integration_gaps(graph: Dict[str, Set[str]]) -> List[Tuple[str, str]]:
    """Identify module pairs with semantic similarity but no dependency link."""
    gaps = []
    modules = list(graph.keys())
    
    for i, mod_a in enumerate(modules):
        for mod_b in modules[i+1:]:
            # Simple heuristic: shared prefix or related domain
            name_a = mod_a.split('/')[-1].lower()
            name_b = mod_b.split('/')[-1].lower()
            
            if any(token in name_a and token in name_b 
                   for token in ['data', 'learn', 'network', 'semantic', 'visual']):
                if mod_b not in graph[mod_a] and mod_a not in graph[mod_b]:
                    gaps.append((mod_a, mod_b))
    
    return gaps

def analyze_module_ecosystem(module_paths: List[str]) -> Dict:
    """Complete dependency analysis of module ecosystem."""
    graph = build_dependency_graph(module_paths)
    orphans = find_orphans(graph, set(module_paths))
    gaps = find_integration_gaps(graph)
    
    return {
        "dependency_graph": dict(graph),
        "orphaned_modules": list(orphans),
        "integration_gaps": gaps,
        "connectivity_ratio": len(set(graph.keys())) / max(len(module_paths), 1)
    }