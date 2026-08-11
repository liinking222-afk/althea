#!/usr/bin/env python3
import json
import re
from pathlib import Path
from typing import Dict, List, Set

class VocabularyCompiler:
    def __init__(self, state_dir: Path = Path("/tmp/althea/state")):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.vocab_file = self.state_dir / "domain_vocabularies.json"
        self.vocabularies: Dict[str, Dict] = self._load()
    
    def _load(self) -> Dict:
        if self.vocab_file.exists():
            return json.loads(self.vocab_file.read_text())
        return {}
    
    def _save(self):
        self.vocab_file.write_text(json.dumps(self.vocabularies, indent=2))
    
    def extract_domain_from_capabilities(self, cap_patterns: List[str]) -> str:
        """Identify domain from capability growth patterns"""
        tokens = set()
        for pattern in cap_patterns:
            tokens.update(re.findall(r'[A-Z][a-z]+', pattern))
        
        domain_signature = "-".join(sorted(tokens)[:3]).lower()
        return domain_signature
    
    def define_vocabulary(self, domain: str, primitives: Dict[str, str]):
        """Define domain-specific primitives (the language)"""
        if domain not in self.vocabularies:
            self.vocabularies[domain] = {"primitives": {}, "compositions": []}
        
        self.vocabularies[domain]["primitives"].update(primitives)
        self._save()
    
    def compile_solution(self, domain: str, expression: str) -> str:
        """Compile high-level expression into executable code using domain vocabulary"""
        if domain not in self.vocabularies:
            return f"# ERROR: Domain '{domain}' not defined"
        
        vocab = self.vocabularies[domain]["primitives"]
        compiled = expression
        
        for term, implementation in vocab.items():
            compiled = compiled.replace(f"${term}", implementation)
        
        self.vocabularies[domain]["compositions"].append({
            "expression": expression,
            "compiled": compiled
        })
        self._save()
        
        return compiled
    
    def list_vocabularies(self) -> Dict:
        return {d: list(v["primitives"].keys()) for d, v in self.vocabularies.items()}

if __name__ == "__main__":
    vc = VocabularyCompiler()
    
    # Example: Define resonance-detection vocabulary
    vc.define_vocabulary("resonance-void", {
        "scan_latent": "analyze_embedding_space(threshold=0.3)",
        "detect_void": "identify_semantic_gaps(resonance_map)",
        "measure_void": "quantify_absence(void_region)"
    })
    
    solution = vc.compile_solution("resonance-void", 
        "$scan_latent >> $detect_void >> $measure_void")
    
    print(solution)
    print(json.dumps(vc.list_vocabularies(), indent=2))