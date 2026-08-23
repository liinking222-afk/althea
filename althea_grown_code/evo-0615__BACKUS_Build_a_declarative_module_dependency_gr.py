#!/usr/bin/env python3
"""Module Composition Reasoner - Declarative dependency graph with type algebra"""
import re
from typing import Dict, Set, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ModuleSignature:
    name: str
    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]
    
    def composes_with(self, other: 'ModuleSignature') -> bool:
        """Algebraic composition: my outputs ⊆ other's inputs"""
        return set(self.outputs).intersection(set(other.inputs)) != set()
    
    def __rshift__(self, other: 'ModuleSignature') -> Optional['ModuleSignature']:
        """Operator overload: self >> other creates composed signature"""
        if not self.composes_with(other):
            return None
        shared = set(self.outputs) & set(other.inputs)
        new_inputs = tuple(set(self.inputs) | (set(other.inputs) - shared))
        new_outputs = tuple(set(other.outputs) | (set(self.outputs) - shared))
        return ModuleSignature(f"{self.name}∘{other.name}", new_inputs, new_outputs)

class CompositionGraph:
    def __init__(self):
        self.modules: Dict[str, ModuleSignature] = {}
        self.edges: Set[Tuple[str, str]] = set()
    
    def register(self, sig: ModuleSignature):
        self.modules[sig.name] = sig
        for other_name, other_sig in self.modules.items():
            if sig.composes_with(other_sig):
                self.edges.add((sig.name, other_name))
            if other_sig.composes_with(sig):
                self.edges.add((other_name, sig.name))
    
    def find_compositions(self, start: str, end: str) -> List[List[str]]:
        """Find all valid composition paths from start to end module"""
        paths = []
        def dfs(current: str, target: str, path: List[str], visited: Set[str]):
            if current == target:
                paths.append(path)
                return
            visited.add(current)
            for src, dst in self.edges:
                if src == current and dst not in visited:
                    dfs(dst, target, path + [dst], visited.copy())
        dfs(start, end, [start], set())
        return paths
    
    def compose_chain(self, path: List[str]) -> Optional[ModuleSignature]:
        """Reduce a path to a single composed signature via >> operator"""
        result = self.modules.get(path[0])
        for name in path[1:]:
            if result is None:
                return None
            result = result >> self.modules[name]
        return result
    
    def export_dot(self) -> str:
        """Export as GraphViz DOT for visualization"""
        lines = ["digraph ModuleComposition {", "  rankdir=LR;"]
        for name, sig in self.modules.items():
            label = f"{name}\\n{sig.inputs}→{sig.outputs}"
            lines.append(f'  "{name}" [label="{label}"];')
        for src, dst in self.edges:
            lines.append(f'  "{src}" -> "{dst}";')
        lines.append("}")
        return "\n".join(lines)

if __name__ == "__main__":
    graph = CompositionGraph()
    graph.register(ModuleSignature("transfer-learning", ("raw_data",), ("features", "model")))
    graph.register(ModuleSignature("temporal-shear", ("memory_fragments",), ("phase_transitions",)))
    graph.register(ModuleSignature("chemistry-lookup", ("element_symbol",), ("properties",)))
    graph.register(ModuleSignature("feature-extractor", ("raw_data",), ("features",)))
    graph.register(ModuleSignature("classifier", ("features",), ("prediction",)))
    
    paths = graph.find_compositions("feature-extractor", "classifier")
    print(f"Composition paths: {paths}")
    if paths:
        composed = graph.compose_chain(paths[0])
        print(f"Algebraic reduction: {composed}")