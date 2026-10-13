#!/usr/bin/env python3
import re
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path

def extract_signature(module_content: str) -> Optional[Tuple[Set[str], Set[str]]]:
    """Parse module for inputs/outputs as algebraic types."""
    inputs = set()
    outputs = set()
    
    # Match INTENT lines for input/output type hints
    intent_match = re.search(r'INTENT:.*?(?:takes?|consumes?|accepts?)\s+([a-z_]+(?:,\s*[a-z_]+)*)', 
                            module_content, re.IGNORECASE)
    if intent_match:
        inputs.update(re.findall(r'[a-z_]+', intent_match.group(1)))
    
    # Match return/output/produces statements
    output_matches = re.findall(r'(?:returns?|outputs?|produces?|emits?)\s+([a-z_]+(?:,\s*[a-z_]+)*)',
                                module_content, re.IGNORECASE)
    for match in output_matches:
        outputs.update(re.findall(r'[a-z_]+', match))
    
    # Parse function signatures for type consistency
    func_sig = re.search(r'def\s+\w+\((.*?)\)\s*->\s*(\w+)', module_content)
    if func_sig:
        params = re.findall(r'(\w+):\s*(\w+)', func_sig.group(1))
        inputs.update(p[1].lower() for p in params)
        outputs.add(func_sig.group(2).lower())
    
    return (inputs, outputs) if inputs or outputs else None

def validate_composition(module_a: str, module_b: str) -> bool:
    """Verify modules compose: output(A) ⊆ input(B) or vice versa."""
    sig_a = extract_signature(module_a)
    sig_b = extract_signature(module_b)
    
    if not sig_a or not sig_b:
        return False
    
    inputs_a, outputs_a = sig_a
    inputs_b, outputs_b = sig_b
    
    # Check if A's outputs match B's inputs (A → B composition)
    forward_compatible = bool(outputs_a & inputs_b)
    # Check if B's outputs match A's inputs (B → A composition)
    backward_compatible = bool(outputs_b & inputs_a)
    
    return forward_compatible or backward_compatible

def analyze_module_algebra(modules_dir: str = ".") -> Dict[str, List[str]]:
    """Build composition graph showing which modules are algebraically composable."""
    modules = {}
    composition_graph = {}
    
    for path in Path(modules_dir).rglob("*.py"):
        content = path.read_text()
        sig = extract_signature(content)
        if sig:
            modules[path.stem] = content
    
    for name_a, content_a in modules.items():
        composable = []
        for name_b, content_b in modules.items():
            if name_a != name_b and validate_composition(content_a, content_b):
                composable.append(name_b)
        composition_graph[name_a] = composable
    
    return composition_graph

if __name__ == "__main__":
    graph = analyze_module_algebra()
    for module, composable_with in sorted(graph.items()):
        if composable_with:
            print(f"{module} ∘ {composable_with}")