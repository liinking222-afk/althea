#!/usr/bin/env python3
"""Vocabulary-First Problem Framing: Define primitives before solutions."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class Primitive:
    name: str
    semantics: str
    composition_rules: List[str]
    examples: List[str]

class VocabularySpace:
    def __init__(self, domain: str):
        self.domain = domain
        self.primitives: Dict[str, Primitive] = {}
        self.compositions: Dict[str, List[str]] = {}
        
    def define(self, name: str, semantics: str, 
               composition_rules: List[str] = None, 
               examples: List[str] = None) -> Primitive:
        """Define a primitive in this vocabulary space."""
        prim = Primitive(
            name=name,
            semantics=semantics,
            composition_rules=composition_rules or [],
            examples=examples or []
        )
        self.primitives[name] = prim
        return prim
    
    def compose(self, composition_name: str, primitives: List[str]) -> bool:
        """Declare a valid composition of primitives."""
        if all(p in self.primitives for p in primitives):
            self.compositions[composition_name] = primitives
            return True
        return False
    
    def express(self, intent: str, using: List[str]) -> Optional[str]:
        """Express intent using declared vocabulary."""
        if not all(p in self.primitives for p in using):
            return None
        return f"{intent} := {' ∘ '.join(using)}"
    
    def serialize(self, path: Path):
        """Persist vocabulary for reuse."""
        data = {
            "domain": self.domain,
            "primitives": {k: asdict(v) for k, v in self.primitives.items()},
            "compositions": self.compositions
        }
        path.write_text(json.dumps(data, indent=2))
    
    @classmethod
    def load(cls, path: Path) -> 'VocabularySpace':
        """Load existing vocabulary space."""
        data = json.loads(path.read_text())
        space = cls(data["domain"])
        for name, pdata in data["primitives"].items():
            space.primitives[name] = Primitive(**pdata)
        space.compositions = data["compositions"]
        return space

if __name__ == "__main__":
    vocab = VocabularySpace("cognitive-evolution")
    vocab.define("observe", "Perceive current state without judgment")
    vocab.define("thread", "Maintain coherence across fragments")
    vocab.define("interpolate", "Generate intermediate forms")
    vocab.compose("evolve", ["observe", "interpolate", "thread"])
    print(vocab.express("meta-growth", ["observe", "thread"]))