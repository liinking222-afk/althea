import hashlib
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set

@dataclass
class SynthesisFingerprint:
    pattern: str
    context_hash: bytes
    invocation_count: int
    token_cost: int

class MemoryDeduplicator:
    def __init__(self):
        self.fingerprints: Dict[bytes, SynthesisFingerprint] = {}
        self.pattern_signatures: Dict[str, Set[bytes]] = defaultdict(set)
        self.total_tokens_saved: int = 0
    
    def hash_context(self, pattern: str, context: str) -> bytes:
        hasher = hashlib.blake2b(digest_size=16)
        hasher.update(pattern.encode('utf-8'))
        hasher.update(b'\x00')
        hasher.update(context.encode('utf-8'))
        return hasher.digest()
    
    def should_synthesize(self, pattern: str, context: str, token_cost: int) -> bool:
        ctx_hash = self.hash_context(pattern, context)
        
        if ctx_hash in self.fingerprints:
            fp = self.fingerprints[ctx_hash]
            fp.invocation_count += 1
            self.total_tokens_saved += token_cost
            return False
        
        self.fingerprints[ctx_hash] = SynthesisFingerprint(
            pattern=pattern,
            context_hash=ctx_hash,
            invocation_count=1,
            token_cost=token_cost
        )
        self.pattern_signatures[pattern].add(ctx_hash)
        return True
    
    def get_redundancy_report(self) -> Dict[str, int]:
        redundant = {}
        for pattern, hashes in self.pattern_signatures.items():
            duplicates = sum(
                self.fingerprints[h].invocation_count - 1 
                for h in hashes
            )
            if duplicates > 0:
                redundant[pattern] = duplicates
        return redundant
    
    def prune_cold_entries(self, threshold: int = 100):
        cold_hashes = [
            h for h, fp in self.fingerprints.items()
            if fp.invocation_count == 1
        ][:threshold]
        
        for h in cold_hashes:
            fp = self.fingerprints.pop(h)
            self.pattern_signatures[fp.pattern].discard(h)

deduplicator = MemoryDeduplicator()