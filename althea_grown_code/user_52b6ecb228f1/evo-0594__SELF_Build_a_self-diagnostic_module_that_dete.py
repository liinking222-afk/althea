#!/usr/bin/env python3
"""AUTOSYNTH Loop Detector - Prevents redundant synthesis cascades"""

from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
import hashlib

class AutosynthThrottler:
    def __init__(self, window_minutes=60, similarity_threshold=0.8, max_instances=3):
        self.window = timedelta(minutes=window_minutes)
        self.similarity_threshold = similarity_threshold
        self.max_instances = max_instances
        self.synthesis_log = deque(maxlen=1000)
        self.pattern_hashes = defaultdict(list)
        
    def signature(self, module_name, description):
        """Generate fuzzy signature for synthesis event"""
        normalized = f"{module_name.lower().strip()}{description[:100].lower()}"
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def should_throttle(self, module_name, description):
        """Returns (should_block, reason)"""
        now = datetime.now()
        sig = self.signature(module_name, description)
        
        # Clean old entries
        cutoff = now - self.window
        self.synthesis_log = deque(
            [e for e in self.synthesis_log if e['timestamp'] > cutoff],
            maxlen=1000
        )
        
        # Check for exact pattern repetition
        recent_sigs = [e['signature'] for e in self.synthesis_log 
                       if e['timestamp'] > cutoff]
        
        if recent_sigs.count(sig) >= self.max_instances:
            return (True, f"Pattern {sig} repeated {recent_sigs.count(sig)} times in {self.window}")
        
        # Log this synthesis
        self.synthesis_log.append({
            'timestamp': now,
            'signature': sig,
            'module': module_name,
            'description': description
        })
        
        return (False, None)
    
    def get_stats(self):
        """Return current synthesis statistics"""
        now = datetime.now()
        cutoff = now - self.window
        recent = [e for e in self.synthesis_log if e['timestamp'] > cutoff]
        
        freq = defaultdict(int)
        for e in recent:
            freq[e['signature']] += 1
            
        return {
            'total_recent': len(recent),
            'unique_patterns': len(freq),
            'most_frequent': sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5],
            'window_minutes': self.window.total_seconds() / 60
        }

# Singleton instance
throttler = AutosynthThrottler()

def check_synthesis(module_name, description):
    return throttler.should_throttle(module_name, description)

def synthesis_stats():
    return throttler.get_stats()