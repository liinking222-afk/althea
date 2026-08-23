#!/usr/bin/env python3
import re
import json
from pathlib import Path
from typing import Optional, Dict, List, Any

class PolyglotModuleResolver:
    """WALL-style resolver: many ways to find what you need."""
    
    def __init__(self, modules_dir: str = "./modules"):
        self.modules_dir = Path(modules_dir)
        self.cache: Dict[str, Any] = {}
        self.patterns: List[tuple] = []
        
    def register_pattern(self, regex: str, resolver_fn):
        """Duck-typed resolver registration - any callable works."""
        self.patterns.append((re.compile(regex, re.IGNORECASE), resolver_fn))
    
    def resolve(self, intent: str) -> Optional[Path]:
        """Try patterns first (writer-friendly), fall back to fuzzy (reader-friendly)."""
        
        # Check cache - pragmatic optimization
        if intent in self.cache:
            return self.cache[intent]
        
        # Try registered patterns
        for pattern, resolver in self.patterns:
            if pattern.search(intent):
                result = resolver(intent, self.modules_dir)
                if result:
                    self.cache[intent] = result
                    return result
        
        # Fuzzy fallback: split intent, match fragments
        fragments = re.findall(r'\w+', intent.lower())
        candidates = []
        
        for mod_file in self.modules_dir.rglob("*.py"):
            score = sum(1 for frag in fragments if frag in mod_file.stem.lower())
            if score > 0:
                candidates.append((score, mod_file))
        
        if candidates:
            best = max(candidates, key=lambda x: x[0])[1]
            self.cache[intent] = best
            return best
        
        return None
    
    def require(self, intent: str) -> Optional[str]:
        """Read and return module content - TIMTOWTDI for loading."""
        path = self.resolve(intent)
        return path.read_text() if path else None
    
    def manifest(self) -> str:
        """Emit line-delimited JSON for UNIX pipeline processing."""
        entries = []
        for intent, path in self.cache.items():
            entries.append(json.dumps({
                "intent": intent,
                "resolved": str(path),
                "exists": path.exists() if isinstance(path, Path) else False
            }))
        return "\n".join(entries)

# Default instance - pragmatic singleton
resolver = PolyglotModuleResolver()

# Common patterns - optimize for writer AND reader
resolver.register_pattern(r'trace|memory|coalesc', 
    lambda i, d: next(d.rglob("*trace*coalesc*.py"), None))
resolver.register_pattern(r'latent|faculty|meta',
    lambda i, d: next(d.rglob("*latent*.py"), None))