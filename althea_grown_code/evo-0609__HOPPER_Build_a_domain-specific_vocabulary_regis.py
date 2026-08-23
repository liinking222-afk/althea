import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class VocabularyRegistry:
    """Define problem vocabularies before writing solutions."""
    
    def __init__(self, storage_path: str = "/tmp/althea_vocabularies.json"):
        self.storage_path = Path(storage_path)
        self.vocabularies: Dict[str, Dict] = self._load()
    
    def _load(self) -> Dict[str, Dict]:
        if self.storage_path.exists():
            return json.loads(self.storage_path.read_text())
        return {}
    
    def _save(self):
        self.storage_path.write_text(json.dumps(self.vocabularies, indent=2))
    
    def define_vocabulary(self, domain: str, primitives: Dict[str, str]):
        """Define the vocabulary of a problem domain."""
        if domain not in self.vocabularies:
            self.vocabularies[domain] = {
                "created": datetime.utcnow().isoformat(),
                "primitives": {},
                "compositions": []
            }
        
        self.vocabularies[domain]["primitives"].update(primitives)
        self.vocabularies[domain]["updated"] = datetime.utcnow().isoformat()
        self._save()
    
    def register_composition(self, domain: str, name: str, uses_primitives: List[str]):
        """Register a solution built from domain primitives."""
        if domain not in self.vocabularies:
            raise ValueError(f"Domain {domain} not defined")
        
        self.vocabularies[domain]["compositions"].append({
            "name": name,
            "primitives": uses_primitives,
            "created": datetime.utcnow().isoformat()
        })
        self._save()
    
    def get_vocabulary(self, domain: str) -> Optional[Dict]:
        """Retrieve vocabulary for a domain."""
        return self.vocabularies.get(domain)
    
    def list_domains(self) -> List[str]:
        """List all defined problem domains."""
        return list(self.vocabularies.keys())
    
    def missing_primitives(self, domain: str, required: List[str]) -> List[str]:
        """Identify which primitives are not yet defined."""
        if domain not in self.vocabularies:
            return required
        defined = set(self.vocabularies[domain]["primitives"].keys())
        return [p for p in required if p not in defined]

# Global registry instance
VOCABULARY = VocabularyRegistry()