"""
autosynth_invariant_validator.py
Validates AUTOSYNTH pattern detection maintains formal invariants
before spawning modules, ensuring correctness over speed.
"""

from dataclasses import dataclass
from typing import Set, Optional
import hashlib


@dataclass(frozen=True)
class PatternInvariant:
    """Immutable invariant conditions for valid AUTOSYNTH patterns."""
    min_pattern_length: int = 3
    max_pattern_length: int = 64
    min_signal_strength: float = 0.3
    required_fields: frozenset = frozenset({'pattern', 'category', 'signal'})


class InvariantValidator:
    """Validates pattern detection maintains correctness invariants."""
    
    def __init__(self, invariant: PatternInvariant):
        self._inv = invariant
        self._validated_hashes: Set[str] = set()
    
    def _hash_pattern(self, pattern: dict) -> str:
        """Pure function: pattern -> hash."""
        key = f"{pattern.get('pattern', '')}:{pattern.get('category', '')}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def _check_preconditions(self, pattern: dict) -> Optional[str]:
        """Returns error message if preconditions violated, None if valid."""
        # Invariant 1: All required fields present
        if not self._inv.required_fields.issubset(pattern.keys()):
            return f"Missing required fields: {self._inv.required_fields - pattern.keys()}"
        
        # Invariant 2: Pattern length bounds
        plen = len(pattern['pattern'])
        if not (self._inv.min_pattern_length <= plen <= self._inv.max_pattern_length):
            return f"Pattern length {plen} violates bounds [{self._inv.min_pattern_length}, {self._inv.max_pattern_length}]"
        
        # Invariant 3: Signal strength threshold
        if pattern['signal'] < self._inv.min_signal_strength:
            return f"Signal strength {pattern['signal']} below threshold {self._inv.min_signal_strength}"
        
        # Invariant 4: No duplicate spawning (idempotence)
        phash = self._hash_pattern(pattern)
        if phash in self._validated_hashes:
            return f"Pattern hash {phash} already validated (duplicate)"
        
        return None
    
    def validate_and_register(self, pattern: dict) -> tuple[bool, str]:
        """
        Post-condition: If True returned, all invariants hold and pattern is registered.
        Returns: (is_valid, message)
        """
        error = self._check_preconditions(pattern)
        if error:
            return False, error
        
        # Register after validation (maintains invariant set consistency)
        phash = self._hash_pattern(pattern)
        self._validated_hashes.add(phash)
        
        return True, f"Pattern validated: {pattern['pattern'][:20]}..."


# Singleton instance with proven-correct default invariants
_validator = InvariantValidator(PatternInvariant())


def validate_autosynth_pattern(pattern: dict) -> tuple[bool, str]:
    """Public interface: validate pattern maintains all invariants."""
    return _validator.validate_and_register(pattern)