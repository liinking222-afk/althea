#!/usr/bin/env python3
"""
/autonomous-synthesis-dedup-filter-0001
Temporal deduplication for autosynth events
"""

import hashlib
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class SynthesisEvent:
    module_path: str
    domain: str
    timestamp: float
    signature: str


class SynthesisDedupFilter:
    def __init__(self, window_seconds: float = 300.0, max_history: int = 1000):
        self.window_seconds = window_seconds
        self.max_history = max_history
        self.history: deque[SynthesisEvent] = deque(maxlen=max_history)
    
    def _compute_signature(self, module_path: str, domain: str, trigger_pattern: str) -> str:
        """Generate semantic fingerprint of synthesis event"""
        content = f"{module_path}::{domain}::{trigger_pattern}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _prune_expired(self, current_time: float) -> None:
        """Remove events outside temporal window"""
        cutoff = current_time - self.window_seconds
        while self.history and self.history[0].timestamp < cutoff:
            self.history.popleft()
    
    def should_synthesize(
        self, 
        module_path: str, 
        domain: str, 
        trigger_pattern: str
    ) -> bool:
        """Returns True if synthesis should proceed, False if duplicate detected"""
        current_time = time.time()
        self._prune_expired(current_time)
        
        signature = self._compute_signature(module_path, domain, trigger_pattern)
        
        # Check for duplicate in window
        for event in self.history:
            if event.signature == signature:
                return False
        
        # Record this synthesis event
        event = SynthesisEvent(
            module_path=module_path,
            domain=domain,
            timestamp=current_time,
            signature=signature
        )
        self.history.append(event)
        return True


# Global singleton instance
_filter = SynthesisDedupFilter()


def check_synthesis_allowed(module_path: str, domain: str, pattern: str) -> bool:
    return _filter.should_synthesize(module_path, domain, pattern)