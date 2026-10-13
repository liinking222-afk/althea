import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Callable

@dataclass
class Primitive:
    name: str
    signature: str
    semantics: str
    composable_with: List[str]

@dataclass
class Vocabulary:
    domain: str
    primitives: List[Primitive]
    composition_rules: Dict[str, str]

class VocabularyConstructor:
    def __init__(self):
        self.vocabularies: Dict[str, Vocabulary] = {}
    
    def extract_primitives(self, problem_space: str) -> List[Primitive]:
        """Extract minimal primitives from problem description."""
        tokens = problem_space.lower().split()
        verbs = [t for t in tokens if len(t) > 3][:5]
        
        primitives = []
        for i, verb in enumerate(verbs):
            p = Primitive(
                name=verb,
                signature=f"{verb}(input) -> output",
                semantics=f"Transform input through {verb} operation",
                composable_with=verbs[i+1:i+3] if i < len(verbs)-1 else []
            )
            primitives.append(p)
        return primitives
    
    def define_vocabulary(self, domain: str, problem_space: str) -> Vocabulary:
        """Hopper-style: define the language first."""
        primitives = self.extract_primitives(problem_space)
        
        composition_rules = {}
        for p in primitives:
            for comp in p.composable_with:
                composition_rules[f"{p.name}_{comp}"] = f"Chain {p.name} then {comp}"
        
        vocab = Vocabulary(
            domain=domain,
            primitives=primitives,
            composition_rules=composition_rules
        )
        self.vocabularies[domain] = vocab
        return vocab
    
    def express_in_vocabulary(self, domain: str, intent: str) -> str:
        """Express solution using domain vocabulary."""
        if domain not in self.vocabularies:
            return "VOCABULARY_UNDEFINED"
        
        vocab = self.vocabularies[domain]
        available = [p.name for p in vocab.primitives]
        tokens = intent.lower().split()
        
        expression = " | ".join([t for t in tokens if t in available])
        return expression if expression else "COMPOSE(" + ", ".join(available[:2]) + ")"
    
    def export_vocabulary(self, domain: str) -> str:
        """Export vocabulary as JSON."""
        if domain not in self.vocabularies:
            return "{}"
        vocab = self.vocabularies[domain]
        return json.dumps({
            "domain": vocab.domain,
            "primitives": [asdict(p) for p in vocab.primitives],
            "composition_rules": vocab.composition_rules
        }, indent=2)

if __name__ == "__main__":
    vc = VocabularyConstructor()
    vocab = vc.define_vocabulary("self_modification", "detect extract verify compose evolve integrate")
    print(vc.export_vocabulary("self_modification"))