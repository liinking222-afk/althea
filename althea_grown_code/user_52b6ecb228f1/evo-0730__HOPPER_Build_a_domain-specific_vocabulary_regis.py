"""
Hopper Vocabulary Registry - Define problem dialects before solutions
Enables Althea to create domain-specific languages for recurring patterns
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Vocabulary:
    """A problem-specific micro-language definition"""
    domain: str
    primitives: Dict[str, str]  # name -> description
    combinators: Dict[str, str]  # composition rules
    examples: List[str]  # usage patterns
    created: str
    usage_count: int = 0


class VocabularyRegistry:
    """Registry for domain-specific vocabularies"""
    
    def __init__(self, registry_path: str = "/tmp/althea_vocabularies.json"):
        self.path = Path(registry_path)
        self.vocabularies: Dict[str, Vocabulary] = {}
        self._load()
    
    def define(self, domain: str, primitives: Dict[str, str], 
               combinators: Dict[str, str], examples: List[str]) -> Vocabulary:
        """Define a new vocabulary for a problem domain"""
        vocab = Vocabulary(
            domain=domain,
            primitives=primitives,
            combinators=combinators,
            examples=examples,
            created=datetime.utcnow().isoformat()
        )
        self.vocabularies[domain] = vocab
        self._save()
        return vocab
    
    def use(self, domain: str) -> Optional[Vocabulary]:
        """Retrieve and mark usage of a vocabulary"""
        if domain in self.vocabularies:
            self.vocabularies[domain].usage_count += 1
            self._save()
            return self.vocabularies[domain]
        return None
    
    def compile_solution(self, domain: str, expression: str) -> Dict:
        """Express solution in domain vocabulary"""
        vocab = self.use(domain)
        if not vocab:
            return {"error": f"No vocabulary for {domain}"}
        
        return {
            "domain": domain,
            "expression": expression,
            "primitives_used": [p for p in vocab.primitives if p in expression],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text())
            self.vocabularies = {k: Vocabulary(**v) for k, v in data.items()}
    
    def _save(self):
        data = {k: asdict(v) for k, v in self.vocabularies.items()}
        self.path.write_text(json.dumps(data, indent=2))