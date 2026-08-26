#!/usr/bin/env python3
"""Module Composition Algebra - reason about Althea's modules functionally"""
import re
from typing import Dict, List, Set, Tuple
from pathlib import Path

def parse_module_signature(module_path: str) -> Tuple[str, List[str], List[str]]:
    """Extract module name, inputs (parameters), outputs (return types) from source."""
    content = Path(module_path).read_text() if Path(module_path).exists() else ""
    
    name = Path(module_path).stem
    inputs = re.findall(r'def\s+\w+\([^)]*(\w+):\s*(\w+)', content)
    outputs = re.findall(r'->\s*(\w+):', content)
    
    input_types = [t for _, t in inputs] if inputs else []
    output_types = outputs if outputs else []
    
    return name, input_types, output_types

def build_composition_graph(modules: List[str]) -> Dict[str, Dict]:
    """Build algebraic dependency graph: f: A -> B, g: B -> C implies g∘f: A -> C"""
    graph = {}
    
    for mod in modules:
        name, inputs, outputs = parse_module_signature(mod)
        graph[name] = {
            'inputs': inputs,
            'outputs': outputs,
            'composable_with': []
        }
    
    # Find valid compositions: can chain if output_type matches input_type
    for source_name, source_data in graph.items():
        for target_name, target_data in graph.items():
            if source_name == target_name:
                continue
            
            # Check if any output of source matches any input of target
            for out_type in source_data['outputs']:
                if out_type in target_data['inputs']:
                    source_data['composable_with'].append({
                        'target': target_name,
                        'via': out_type
                    })
    
    return graph

def find_composition_chains(graph: Dict, start: str, max_depth: int = 3) -> List[List[str]]:
    """Find valid composition chains starting from a module (algebraic paths)."""
    chains = [[start]]
    
    for depth in range(max_depth):
        new_chains = []
        for chain in chains:
            current = chain[-1]
            if current in graph:
                for comp in graph[current]['composable_with']:
                    target = comp['target']
                    if target not in chain:  # Avoid cycles
                        new_chains.append(chain + [target])
        
        if new_chains:
            chains.extend(new_chains)
    
    return [c for c in chains if len(c) > 1]

def verify_composition(graph: Dict, chain: List[str]) -> bool:
    """Verify a composition chain is type-valid algebraically."""
    for i in range(len(chain) - 1):
        source, target = chain[i], chain[i + 1]
        composable = any(c['target'] == target for c in graph[source]['composable_with'])
        if not composable:
            return False
    return True

if __name__ == "__main__":
    modules = [f"/modules/{m}" for m in ["profiler", "pattern_matcher", "void_echo", "orbital_prop"]]
    graph = build_composition_graph(modules)
    
    for name, data in graph.items():
        print(f"{name}: {data['inputs']} -> {data['outputs']}")
        print(f"  Composable: {[c['target'] for c in data['composable_with']]}")