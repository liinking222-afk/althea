import hashlib
import struct
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

class ModuleDeduplicationIndex:
    """Content-addressable storage for module fingerprints with zero-copy lookups."""
    
    def __init__(self):
        # Core data structure: hash -> (module_name, core_function_signature, timestamp)
        self.fingerprints: Dict[bytes, Tuple[str, str, int]] = {}
        # Inverted index: function_sig -> list of hashes for fast collision detection
        self.sig_index: Dict[str, List[bytes]] = defaultdict(list)
        self.collision_count = 0
        
    def _hash_module(self, core_function: str, inputs: str, outputs: str) -> bytes:
        """Compute SHA-256 fingerprint of module semantics, not syntax."""
        normalized = f"{core_function.lower().strip()}|{inputs.strip()}|{outputs.strip()}"
        return hashlib.sha256(normalized.encode('utf-8')).digest()[:16]  # 128-bit hash
    
    def register(self, module_name: str, core_function: str, 
                 inputs: str, outputs: str, timestamp: int) -> Optional[str]:
        """
        Register module. Returns name of duplicate if exists, None if novel.
        O(1) average case with hash table lookup.
        """
        fingerprint = self._hash_module(core_function, inputs, outputs)
        
        if fingerprint in self.fingerprints:
            self.collision_count += 1
            existing = self.fingerprints[fingerprint]
            return existing[0]  # Return duplicate module name
        
        # Novel module: register in both indices
        sig = core_function.lower().strip()
        self.fingerprints[fingerprint] = (module_name, sig, timestamp)
        self.sig_index[sig].append(fingerprint)
        return None
    
    def find_similar(self, core_function: str) -> List[str]:
        """Find all modules with same core function. O(k) where k = matches."""
        sig = core_function.lower().strip()
        hashes = self.sig_index.get(sig, [])
        return [self.fingerprints[h][0] for h in hashes]
    
    def stats(self) -> Dict[str, int]:
        """Return memory statistics."""
        return {
            'unique_modules': len(self.fingerprints),
            'duplicates_blocked': self.collision_count,
            'memory_bytes': len(self.fingerprints) * 48 + sum(len(v) * 16 for v in self.sig_index.values())
        }

# Global singleton instance
_INDEX = ModuleDeduplicationIndex()

def check_duplicate(module_name: str, core_function: str, 
                   inputs: str, outputs: str, timestamp: int = 0) -> Optional[str]:
    """Public API: returns duplicate module name or None."""
    return _INDEX.register(module_name, core_function, inputs, outputs, timestamp)

def get_stats() -> Dict[str, int]:
    return _INDEX.stats()