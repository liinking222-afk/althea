import hashlib
import json
from typing import Any, Dict, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, field

@dataclass
class CompressionStats:
    eliminated: int = 0
    passed: int = 0
    bytes_saved: int = 0

class MessageCompressor:
    """WOZ-inspired compression: every message must earn its transmission."""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.signature_cache: Dict[str, Tuple[int, Any]] = {}
        self.handler_windows: Dict[str, Set[str]] = defaultdict(set)
        self.stats = CompressionStats()
        self.sequence = 0
    
    def _structural_hash(self, payload: Any) -> str:
        """Hash by structure, not identity. Same shape = same hash."""
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.blake2b(canonical.encode(), digest_size=16).hexdigest()
    
    def _semantic_distance(self, h1: str, h2: str) -> int:
        """Hamming distance between hashes as semantic proximity measure."""
        return sum(c1 != c2 for c1, c2 in zip(h1, h2))
    
    def should_transmit(self, handler_id: str, payload: Any) -> Tuple[bool, Optional[str]]:
        """Returns (should_send, reason)"""
        sig = self._structural_hash(payload)
        window = self.handler_windows[handler_id]
        
        # Exact duplicate in window
        if sig in window:
            self.stats.eliminated += 1
            payload_size = len(json.dumps(payload, default=str))
            self.stats.bytes_saved += payload_size
            return False, "exact_duplicate"
        
        # Near-duplicate detection (Hamming distance < 4)
        for cached_sig in window:
            if self._semantic_distance(sig, cached_sig) < 4:
                self.stats.eliminated += 1
                return False, "semantic_duplicate"
        
        # Add to window, evict oldest if full
        window.add(sig)
        if len(window) > self.window_size:
            window.pop()
        
        self.signature_cache[sig] = (self.sequence, payload)
        self.sequence += 1
        self.stats.passed += 1
        return True, None
    
    def compression_ratio(self) -> float:
        """How much are we squeezing out?"""
        total = self.stats.eliminated + self.stats.passed
        return self.stats.eliminated / total if total > 0 else 0.0
    
    def reset_handler(self, handler_id: str):
        """Clear window for specific handler."""
        self.handler_windows[handler_id].clear()

# Integration hook
def compress_message_stream(compressor: MessageCompressor, handler_id: str, messages):
    """Generator that yields only semantically novel messages."""
    for msg in messages:
        should_send, reason = compressor.should_transmit(handler_id, msg)
        if should_send:
            yield msg