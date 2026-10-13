#!/usr/bin/env python3
"""
ALTHEA MODULE: autosynth_deduplication_tracker
Tracks AUTOSYNTH module generation patterns and flags duplicates within a time window.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

class AutosynthDeduplicationTracker:
    def __init__(self, memory_path="data/autosynth_memory.json", window_hours=24):
        self.memory_path = Path(memory_path)
        self.window_hours = window_hours
        self.memory = self._load_memory()
        
    def _load_memory(self):
        if self.memory_path.exists():
            with open(self.memory_path, 'r') as f:
                return json.load(f)
        return {"patterns": {}, "duplicate_events": []}
    
    def _save_memory(self):
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_path, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def _pattern_signature(self, pattern_name, domain):
        """Create hash signature for pattern+domain combination"""
        key = f"{pattern_name}::{domain}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    def check_and_record(self, pattern_name, domain, module_id):
        """Returns (is_duplicate: bool, duplicate_count: int)"""
        sig = self._pattern_signature(pattern_name, domain)
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=self.window_hours)
        
        # Clean old entries
        if sig in self.memory["patterns"]:
            self.memory["patterns"][sig] = [
                entry for entry in self.memory["patterns"][sig]
                if datetime.fromisoformat(entry["timestamp"]) > cutoff
            ]
        
        # Check for duplicates
        recent = self.memory["patterns"].get(sig, [])
        is_duplicate = len(recent) > 0
        
        # Record this occurrence
        if sig not in self.memory["patterns"]:
            self.memory["patterns"][sig] = []
        
        self.memory["patterns"][sig].append({
            "timestamp": now.isoformat(),
            "module_id": module_id,
            "pattern": pattern_name,
            "domain": domain
        })
        
        if is_duplicate:
            self.memory["duplicate_events"].append({
                "timestamp": now.isoformat(),
                "signature": sig,
                "count": len(recent) + 1
            })
        
        self._save_memory()
        return is_duplicate, len(recent) + 1

if __name__ == "__main__":
    tracker = AutosynthDeduplicationTracker()
    is_dup, count = tracker.check_and_record("transfer-learning", "machine-learning", "4325")
    print(f"Duplicate: {is_dup}, Occurrence count: {count}")