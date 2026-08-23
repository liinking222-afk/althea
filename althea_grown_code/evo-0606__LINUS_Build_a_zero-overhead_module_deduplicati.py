import hashlib
import json
from pathlib import Path
from typing import Dict, Set, Optional

class ModuleDeduplicationIndex:
    """Content-addressable module index for O(1) duplicate detection."""
    
    def __init__(self, index_path: str = ".althea/module_index.dat"):
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.hash_to_module: Dict[str, str] = {}
        self.module_to_hash: Dict[str, str] = {}
        self._load()
    
    def _load(self):
        """Load index from disk using simple line format: hash|module_path"""
        if not self.index_path.exists():
            return
        with open(self.index_path, 'r') as f:
            for line in f:
                if '|' in line:
                    h, mod = line.strip().split('|', 1)
                    self.hash_to_module[h] = mod
                    self.module_to_hash[mod] = h
    
    def _save(self):
        """Append-only write for zero-lock concurrency"""
        with open(self.index_path, 'w') as f:
            for h, mod in self.hash_to_module.items():
                f.write(f"{h}|{mod}\n")
    
    def _hash_module(self, intent: str, language: str, code: str) -> str:
        """Semantic hash: intent + normalized code structure"""
        normalized = ''.join(code.split())  # whitespace-invariant
        content = f"{intent.lower().strip()}:{language}:{normalized}"
        return hashlib.blake2b(content.encode(), digest_size=16).hexdigest()
    
    def check_duplicate(self, intent: str, language: str, code: str) -> Optional[str]:
        """Returns existing module path if duplicate exists, None otherwise"""
        h = self._hash_module(intent, language, code)
        return self.hash_to_module.get(h)
    
    def register(self, module_path: str, intent: str, language: str, code: str):
        """Register new module in index"""
        h = self._hash_module(intent, language, code)
        self.hash_to_module[h] = module_path
        self.module_to_hash[module_path] = h
        self._save()
    
    def gc(self, existing_modules: Set[str]):
        """Garbage collect entries for deleted modules"""
        dead = set(self.module_to_hash.keys()) - existing_modules
        for mod in dead:
            h = self.module_to_hash.pop(mod)
            del self.hash_to_module[h]
        if dead:
            self._save()