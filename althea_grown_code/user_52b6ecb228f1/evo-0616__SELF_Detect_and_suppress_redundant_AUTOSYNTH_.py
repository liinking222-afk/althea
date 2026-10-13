#!/usr/bin/env python3
"""AUTOSYNTH Deduplication Registry - Prevents redundant module generation."""

import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Set

class AutosynthRegistry:
    def __init__(self, window_hours: int = 24, registry_path: str = "/tmp/althea_autosynth_registry.json"):
        self.window_hours = window_hours
        self.registry_path = Path(registry_path)
        self.registry: Dict[str, dict] = self._load_registry()
    
    def _load_registry(self) -> Dict[str, dict]:
        """Load existing registry or create new."""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_registry(self):
        """Persist registry to disk."""
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def _prune_expired(self):
        """Remove entries older than window."""
        cutoff = datetime.now() - timedelta(hours=self.window_hours)
        self.registry = {
            sig: data for sig, data in self.registry.items()
            if datetime.fromisoformat(data['timestamp']) > cutoff
        }
    
    def compute_signature(self, module_description: str, domain: str) -> str:
        """Generate semantic hash of module intent."""
        normalized = f"{domain.lower().strip()}:{module_description.lower().strip()}"
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def is_redundant(self, module_description: str, domain: str) -> bool:
        """Check if this module was recently synthesized."""
        self._prune_expired()
        signature = self.compute_signature(module_description, domain)
        return signature in self.registry
    
    def register(self, module_description: str, domain: str, module_path: str):
        """Record a newly synthesized module."""
        signature = self.compute_signature(module_description, domain)
        self.registry[signature] = {
            'description': module_description,
            'domain': domain,
            'path': module_path,
            'timestamp': datetime.now().isoformat(),
            'count': self.registry.get(signature, {}).get('count', 0) + 1
        }
        self._save_registry()
    
    def get_recent_duplicates(self) -> Set[str]:
        """Return signatures that appeared multiple times."""
        self._prune_expired()
        return {sig for sig, data in self.registry.items() if data['count'] > 1}

if __name__ == "__main__":
    registry = AutosynthRegistry(window_hours=24)
    desc = "Transfer Learning (machine-learning). Pretrain, freeze features, swap head"
    
    if registry.is_redundant(desc, "machine-learning"):
        print(f"BLOCKED: Redundant synthesis detected")
    else:
        print(f"ALLOWED: Novel synthesis")
        registry.register(desc, "machine-learning", "/autonomous-transfer-learning-new")