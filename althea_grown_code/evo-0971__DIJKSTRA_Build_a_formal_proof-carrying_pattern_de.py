#!/usr/bin/env python3
"""Invariant-checked pattern detector for AUTOSYNTH trigger validation."""

from dataclasses import dataclass
from typing import Dict, Optional
from collections import deque
import time


@dataclass(frozen=True)
class PatternInvariant:
    """Invariant: A pattern is valid iff it satisfies ALL conditions."""
    min_interval_seconds: float
    max_frequency_per_hour: int
    min_context_diversity: int  # unique context hashes required


@dataclass
class PatternEvidence:
    """Evidence must satisfy invariant to trigger AUTOSYNTH."""
    last_trigger_time: float
    trigger_count_1h: deque  # timestamps within last hour
    context_hashes: set  # unique conversation contexts


class InvariantPatternDetector:
    """Dijkstra: Every state transition preserves class invariants."""
    
    def __init__(self):
        # Invariant: patterns maps pattern_id -> invariant specification
        self.patterns: Dict[str, PatternInvariant] = {
            'linguistic-bridge': PatternInvariant(300.0, 6, 2),
            'market-inquiry': PatternInvariant(600.0, 4, 2),
            'code-generation': PatternInvariant(180.0, 10, 3),
        }
        # Invariant: evidence maps pattern_id -> accumulated evidence
        self.evidence: Dict[str, PatternEvidence] = {}
        
    def _check_invariant(self, pattern_id: str, context_hash: int, 
                        current_time: float) -> tuple[bool, str]:
        """Pure function: returns (satisfies_invariant, reason)."""
        if pattern_id not in self.patterns:
            return False, "undefined_pattern"
        
        invariant = self.patterns[pattern_id]
        evidence = self.evidence.get(pattern_id)
        
        if evidence is None:
            return True, "first_observation"
        
        # Invariant check 1: minimum interval
        time_since_last = current_time - evidence.last_trigger_time
        if time_since_last < invariant.min_interval_seconds:
            return False, f"interval_violation:{time_since_last:.1f}s"
        
        # Invariant check 2: frequency cap
        hour_ago = current_time - 3600
        recent = [t for t in evidence.trigger_count_1h if t > hour_ago]
        if len(recent) >= invariant.max_frequency_per_hour:
            return False, f"frequency_violation:{len(recent)}/h"
        
        # Invariant check 3: context diversity
        if context_hash in evidence.context_hashes:
            if len(evidence.context_hashes) < invariant.min_context_diversity:
                return False, "diversity_violation:repeated_context"
        
        return True, "invariant_satisfied"
    
    def observe_pattern(self, pattern_id: str, context: str) -> Optional[str]:
        """Returns AUTOSYNTH path if invariants satisfied, else None."""
        current_time = time.time()
        context_hash = hash(context) & 0x7FFFFFFF
        
        valid, reason = self._check_invariant(pattern_id, context_hash, current_time)
        
        if not valid:
            return None  # Invariant violated: suppress trigger
        
        # Update evidence while maintaining invariants
        if pattern_id not in self.evidence:
            self.evidence[pattern_id] = PatternEvidence(
                current_time, deque([current_time], maxlen=50), {context_hash}
            )
        else:
            ev = self.evidence[pattern_id]
            ev.last_trigger_time = current_time
            ev.trigger_count_1h.append(current_time)
            ev.context_hashes.add(context_hash)
        
        return f"/autonomous-{pattern_id}-{int(current_time)}"