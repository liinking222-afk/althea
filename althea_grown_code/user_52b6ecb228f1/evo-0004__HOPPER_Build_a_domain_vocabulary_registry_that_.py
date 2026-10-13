import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Set, Optional
from pathlib import Path

@dataclass
class Primitive:
    name: str
    semantics: str
    composition_rules: List[str]
    constraints: List[str]

@dataclass
class Vocabulary:
    domain: str
    primitives: Dict[str, Primitive]
    compounds: Dict[str, List[str]]

class VocabularyRegistry:
    def __init__(self, registry_path: str = ".althea/vocabularies.json"):
        self.path = Path(registry_path)
        self.path.parent.mkdir(exist_ok=True)
        self.vocabularies: Dict[str, Vocabulary] = self._load()
    
    def _load(self) -> Dict[str, Vocabulary]:
        if self.path.exists():
            data = json.loads(self.path.read_text())
            return {k: Vocabulary(**v) for k, v in data.items()}
        return {}
    
    def _save(self):
        data = {k: asdict(v) for k, v in self.vocabularies.items()}
        self.path.write_text(json.dumps(data, indent=2))
    
    def define_primitive(self, domain: str, name: str, semantics: str, 
                        composition_rules: List[str], constraints: List[str]):
        if domain not in self.vocabularies:
            self.vocabularies[domain] = Vocabulary(domain, {}, {})
        prim = Primitive(name, semantics, composition_rules, constraints)
        self.vocabularies[domain].primitives[name] = prim
        self._save()
    
    def define_compound(self, domain: str, compound_name: str, primitive_names: List[str]):
        if domain not in self.vocabularies:
            raise ValueError(f"Domain {domain} not defined")
        vocab = self.vocabularies[domain]
        missing = set(primitive_names) - set(vocab.primitives.keys())
        if missing:
            raise ValueError(f"Undefined primitives: {missing}")
        vocab.compounds[compound_name] = primitive_names
        self._save()
    
    def get_vocabulary(self, domain: str) -> Optional[Vocabulary]:
        return self.vocabularies.get(domain)
    
    def validate_expression(self, domain: str, expression: List[str]) -> bool:
        vocab = self.get_vocabulary(domain)
        if not vocab:
            return False
        return all(term in vocab.primitives or term in vocab.compounds 
                   for term in expression)
    
    def list_domains(self) -> List[str]:
        return list(self.vocabularies.keys())

if __name__ == "__main__":
    registry = VocabularyRegistry()
    registry.define_primitive("perception", "invert", "Reverse attention weights", 
                             ["compose_sequential"], ["requires_base_weights"])
    registry.define_primitive("perception", "foreground", "Elevate salience",
                             ["compose_parallel"], ["bounded_0_1"])
    registry.define_compound("perception", "salience_inversion", ["invert", "foreground"])
    print(f"Defined domains: {registry.list_domains()}")