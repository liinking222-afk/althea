#!/usr/bin/env python3
import json
import sys
from collections import deque
from hashlib import sha256

class RecursionDriftMonitor:
    def __init__(self, max_depth=10, drift_threshold=0.3):
        self.max_depth = max_depth
        self.drift_threshold = drift_threshold
        self.stack = deque(maxlen=max_depth)
        self.drift_alerts = []
    
    def semantic_hash(self, content):
        """Generate semantic fingerprint of processing state."""
        normalized = json.dumps(content, sort_keys=True) if isinstance(content, dict) else str(content)
        return sha256(normalized.encode()).hexdigest()[:16]
    
    def calculate_drift(self, hash1, hash2):
        """Calculate hamming distance as proxy for semantic drift."""
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2)) / len(hash1)
    
    def trace_step(self, context, metadata=None):
        """Record a processing step and analyze drift."""
        current_hash = self.semantic_hash(context)
        depth = len(self.stack)
        
        if depth > 0:
            parent_hash = self.stack[-1]['hash']
            drift = self.calculate_drift(current_hash, parent_hash)
            expected_drift = self.drift_threshold * (1 + depth / self.max_depth)
            
            if drift < expected_drift and depth > 3:
                alert = {
                    'depth': depth,
                    'drift': drift,
                    'expected': expected_drift,
                    'ratio': drift / expected_drift if expected_drift > 0 else 0,
                    'hash': current_hash,
                    'parent_hash': parent_hash
                }
                self.drift_alerts.append(alert)
                return {'status': 'SHALLOW_RECURSION', 'alert': alert}
        
        self.stack.append({'hash': current_hash, 'context': metadata or {}})
        return {'status': 'OK', 'depth': depth, 'hash': current_hash}
    
    def pop_step(self):
        """Exit current processing level."""
        if self.stack:
            return self.stack.pop()
        return None
    
    def get_report(self):
        """Generate drift analysis report."""
        return {
            'current_depth': len(self.stack),
            'shallow_loops_detected': len(self.drift_alerts),
            'alerts': self.drift_alerts[-5:],
            'stack_hashes': [s['hash'] for s in self.stack]
        }

if __name__ == '__main__':
    monitor = RecursionDriftMonitor()
    for line in sys.stdin:
        event = json.loads(line.strip())
        result = monitor.trace_step(event.get('context'), event.get('metadata'))
        print(json.dumps(result))
        if event.get('action') == 'pop':
            monitor.pop_step()
        elif event.get('action') == 'report':
            print(json.dumps(monitor.get_report()))