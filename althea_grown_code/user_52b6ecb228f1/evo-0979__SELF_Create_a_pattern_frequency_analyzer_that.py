#!/usr/bin/env python3
"""
ALTHEA Module: autosynth_dedup_guard.py
Monitors AUTOSYNTH pattern triggers and suppresses redundant synthesis.
"""

import json
import time
from collections import defaultdict
from pathlib import Path


class AutosynthDedupGuard:
    def __init__(self, window_seconds=3600, threshold=3):
        self.window = window_seconds
        self.threshold = threshold
        self.pattern_log = defaultdict(list)
        self.suppression_list = set()
        
    def record_trigger(self, pattern_name):
        """Record a pattern trigger attempt."""
        now = time.time()
        self.pattern_log[pattern_name].append(now)
        self._cleanup_old_entries(pattern_name, now)
        
        if len(self.pattern_log[pattern_name]) >= self.threshold:
            self.suppression_list.add(pattern_name)
            return True  # suppress
        return False  # allow
    
    def _cleanup_old_entries(self, pattern_name, now):
        """Remove entries outside time window."""
        cutoff = now - self.window
        self.pattern_log[pattern_name] = [
            t for t in self.pattern_log[pattern_name] if t > cutoff
        ]
        
        if len(self.pattern_log[pattern_name]) < self.threshold:
            self.suppression_list.discard(pattern_name)
    
    def should_suppress(self, pattern_name):
        """Check if pattern should be suppressed."""
        return pattern_name in self.suppression_list
    
    def get_stats(self):
        """Return current deduplication statistics."""
        return {
            "active_suppressions": list(self.suppression_list),
            "pattern_frequencies": {
                k: len(v) for k, v in self.pattern_log.items()
            }
        }
    
    def reset_pattern(self, pattern_name):
        """Manually reset suppression for a pattern."""
        self.pattern_log[pattern_name].clear()
        self.suppression_list.discard(pattern_name)


# Global instance
_guard = AutosynthDedupGuard()

def check_and_record(pattern_name):
    """Main interface: returns True if should suppress."""
    return _guard.record_trigger(pattern_name)

def get_dedup_stats():
    return _guard.get_stats()