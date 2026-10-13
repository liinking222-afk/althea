#!/usr/bin/env python3
import json
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Set

@dataclass
class ModuleSignature:
    name: str
    inputs: List[str]
    outputs: List[str]
    side_effects: List[str]
    
    def compose_with(self, other: 'ModuleSignature') -> Optional['ModuleSignature']:
        """Check if modules can compose (this.output → other.input)"""
        output_set = set(self.outputs)
        input_set = set(other.inputs)
        
        if not input_set.issubset(output_set):
            return None
        
        return ModuleSignature(
            name=f"{self.name}∘{other.name}",
            inputs=self.inputs,
            outputs=other.outputs,
            side_effects=self.side_effects + other.side_effects
        )
    
    def is_pure(self) -> bool:
        return len(self.side_effects) == 0
    
    def commutes_with(self, other: 'ModuleSignature') -> bool:
        """Check if modules commute (can run in any order)"""
        my_effects = set(self.side_effects + self.outputs)
        other_effects = set(other.side_effects + other.outputs)
        my_reads = set(self.inputs)
        other_reads = set(other.inputs)
        
        return not (my_effects & other_reads or other_effects & my_reads)

def analyze_pipeline(signatures: List[Dict[str, Any]]) -> Dict[str, Any]:
    modules = [ModuleSignature(**sig) for sig in signatures]
    
    # Check purity
    pure_modules = [m.name for m in modules if m.is_pure()]
    
    # Find composable pairs
    compositions = []
    for i, m1 in enumerate(modules):
        for j, m2 in enumerate(modules[i+1:], i+1):
            if comp := m1.compose_with(m2):
                compositions.append({"pair": [i, j], "result": asdict(comp)})
    
    # Find commutative pairs
    commutative = []
    for i, m1 in enumerate(modules):
        for j, m2 in enumerate(modules[i+1:], i+1):
            if m1.commutes_with(m2):
                commutative.append([i, j])
    
    return {
        "pure_modules": pure_modules,
        "composable_pairs": compositions,
        "commutative_pairs": commutative,
        "total_side_effects": sum(len(m.side_effects) for m in modules)
    }

if __name__ == "__main__":
    for line in sys.stdin:
        request = json.loads(line)
        result = analyze_pipeline(request["signatures"])
        print(json.dumps({"analysis": result}))
        sys.stdout.flush()