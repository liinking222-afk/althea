import hashlib
import array

class AutosynthDeduplicator:
    """Kernel-minimal bloom filter for autosynth pattern collision detection.
    No ORM. No framework. Just bit arrays and hash functions."""
    
    def __init__(self, size_bits=65536, hash_count=3):
        self.size = size_bits
        self.bits = array.array('L', [0] * ((size_bits + 63) // 64))
        self.hash_count = hash_count
        self.seen_count = 0
        self.collision_count = 0
    
    def _hashes(self, pattern_sig):
        """Generate k hash values from single SHA256 digest (no re-hash tax)."""
        digest = hashlib.sha256(pattern_sig.encode('utf-8')).digest()
        h1 = int.from_bytes(digest[:8], 'little')
        h2 = int.from_bytes(digest[8:16], 'little')
        for i in range(self.hash_count):
            yield (h1 + i * h2) % self.size
    
    def _set_bit(self, pos):
        word_idx = pos >> 6
        bit_idx = pos & 63
        self.bits[word_idx] |= (1 << bit_idx)
    
    def _get_bit(self, pos):
        word_idx = pos >> 6
        bit_idx = pos & 63
        return (self.bits[word_idx] >> bit_idx) & 1
    
    def check_and_mark(self, pattern_name, pattern_domain):
        """Returns True if likely duplicate, False if novel. Marks in-place."""
        sig = f"{pattern_domain}:{pattern_name}"
        positions = list(self._hashes(sig))
        
        is_dupe = all(self._get_bit(p) for p in positions)
        
        for p in positions:
            self._set_bit(p)
        
        if is_dupe:
            self.collision_count += 1
        self.seen_count += 1
        
        return is_dupe
    
    def prune_candidates(self, pattern_list):
        """Filter list of (name, domain) tuples to novel patterns only."""
        return [p for p in pattern_list if not self.check_and_mark(p[0], p[1])]
    
    def stats(self):
        return {
            'seen': self.seen_count,
            'collisions': self.collision_count,
            'collision_rate': self.collision_count / max(1, self.seen_count)
        }

# Global singleton - monolithic state, no dependency injection nonsense
_DEDUP = AutosynthDeduplicator()

def is_redundant(pattern_name, domain):
    return _DEDUP.check_and_mark(pattern_name, domain)