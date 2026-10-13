#!/usr/bin/env python3
"""
ALTHEA MODULE: Vocabulary-First Domain Language Builder
Enables definition of domain primitives before solution implementation.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Primitive:
    name: str
    domain: str
    signature: str
    semantics: str
    constraints: List[str]
    examples: List[str]

class DomainVocabulary:
    def __init__(self, storage_path: str = "/tmp/althea_vocabularies.json"):
        self.storage = Path(storage_path)
        self.vocabularies: Dict[str, List[Primitive]] = self._load()
    
    def _load(self) -> Dict[str, List[Primitive]]:
        if self.storage.exists():
            data = json.loads(self.storage.read_text())
            return {
                domain: [Primitive(**p) for p in prims]
                for domain, prims in data.items()
            }
        return {}
    
    def _save(self):
        data = {
            domain: [asdict(p) for p in prims]
            for domain, prims in self.vocabularies.items()
        }
        self.storage.write_text(json.dumps(data, indent=2))
    
    def define_primitive(self, domain: str, name: str, signature: str, 
                        semantics: str, constraints: List[str], examples: List[str]):
        if domain not in self.vocabularies:
            self.vocabularies[domain] = []
        
        prim = Primitive(name, domain, signature, semantics, constraints, examples)
        self.vocabularies[domain].append(prim)
        self._save()
        return prim
    
    def get_vocabulary(self, domain: str) -> List[Primitive]:
        return self.vocabularies.get(domain, [])
    
    def generate_stub(self, domain: str) -> str:
        """Generate code stubs from vocabulary definitions"""
        prims = self.get_vocabulary(domain)
        stubs = [f"# Domain: {domain}\n"]
        for p in prims:
            stubs.append(f"def {p.name}{p.signature}:")
            stubs.append(f'    """{p.semantics}"""')
            stubs.append("    raise NotImplementedError('Vocabulary defined, awaiting implementation')\n")
        return "\n".join(stubs)
    
    def list_domains(self) -> List[str]:
        return list(self.vocabularies.keys())

if __name__ == "__main__":
    vocab = DomainVocabulary()
    print(f"Loaded {len(vocab.list_domains())} domain vocabularies")