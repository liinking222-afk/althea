import json
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Primitive:
    term: str
    definition: str
    synonyms: List[str]
    antonyms: List[str]
    domain: str

@dataclass
class Vocabulary:
    name: str
    domain: str
    primitives: Dict[str, Primitive]
    created: str
    version: str

class VocabularyRegistry:
    def __init__(self, registry_path: str = "/tmp/althea_vocabularies.json"):
        self.registry_path = Path(registry_path)
        self.vocabularies: Dict[str, Vocabulary] = {}
        self._load()
    
    def _load(self):
        if self.registry_path.exists():
            data = json.loads(self.registry_path.read_text())
            for name, vocab_data in data.items():
                prims = {k: Primitive(**v) for k, v in vocab_data['primitives'].items()}
                vocab_data['primitives'] = prims
                self.vocabularies[name] = Vocabulary(**vocab_data)
    
    def _save(self):
        data = {}
        for name, vocab in self.vocabularies.items():
            vocab_dict = asdict(vocab)
            data[name] = vocab_dict
        self.registry_path.write_text(json.dumps(data, indent=2))
    
    def define_vocabulary(self, name: str, domain: str, primitives: List[Primitive]) -> Vocabulary:
        vocab = Vocabulary(
            name=name,
            domain=domain,
            primitives={p.term: p for p in primitives},
            created=datetime.utcnow().isoformat(),
            version="1.0.0"
        )
        self.vocabularies[name] = vocab
        self._save()
        return vocab
    
    def get_vocabulary(self, name: str) -> Vocabulary:
        return self.vocabularies.get(name)
    
    def find_primitives_by_domain(self, domain: str) -> Dict[str, Set[str]]:
        result = {}
        for vocab in self.vocabularies.values():
            if vocab.domain == domain:
                result[vocab.name] = set(vocab.primitives.keys())
        return result
    
    def check_vocabulary_overlap(self, vocab1: str, vocab2: str) -> Set[str]:
        v1 = self.vocabularies.get(vocab1)
        v2 = self.vocabularies.get(vocab2)
        if not v1 or not v2:
            return set()
        return set(v1.primitives.keys()) & set(v2.primitives.keys())

registry = VocabularyRegistry()