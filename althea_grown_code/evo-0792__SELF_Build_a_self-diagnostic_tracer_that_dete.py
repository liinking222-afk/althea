INTENT: Build a self-diagnostic tracer that detects when Althea generates redundant or duplicate synthesis patterns and emits suppression signals to prevent wasteful re-creation.

LANGUAGE: python

```python
#!/usr/bin/env python3
"""
ALTHEA DEDUPLICATION SENTINEL
Tracks synthesis fingerprints and blocks redundant module generation.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Set, Optional

class DeduplicationSentinel:
    def __init__(self, memory_path: str = "/tmp/althea_dedup.json"):
        self.memory_path = Path(memory_path)
        self.fingerprints: Dict[str, float] = {}
        self.load_state()
    
    def load_state(self):
        """Load existing fingerprint memory."""
        if self.memory_path.exists():
            try:
                with open(self.memory_path) as f:
                    self.fingerprints = json.load(f)
            except:
                self.fingerprints = {}
    
    def save_state(self):
        """Persist fingerprint memory."""
        with open(self.memory_path, 'w') as f:
            json.dump(self.fingerprints, f)
    
    def fingerprint(self, intent: str, context: str) -> str:
        """Generate semantic fingerprint from intent and context."""
        normalized = f"{intent.lower().strip()}::{context.lower().strip()}"
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def is_redundant(self, intent: str, context: str, threshold_hours: float = 24.0) -> bool:
        """Check if this synthesis would be redundant."""
        fp = self.fingerprint(intent, context)
        if fp in self.fingerprints:
            elapsed = time.time() - self.fingerprints[fp]
            if elapsed < threshold_hours * 3600:
                return True
        return False
    
    def register(self, intent: str, context: str):
        """Register a new synthesis to prevent near-term duplication."""
        fp = self.fingerprint(intent, context)
        self.fingerprints[fp] = time.time()
        self.save_state()
    
    def prune(self, max_age_hours: float = 168.0):
        """Remove old fingerprints to prevent unbounded growth."""
        cutoff = time.time() - (max_age_hours * 3600)
        self.fingerprints = {
            fp: ts for fp, ts in self.fingerprints.items() if ts > cutoff
        }
        self.save_state()

def check_redundancy(intent: str, context: str) -> bool:
    """Main entry point: returns True if synthesis should be supp