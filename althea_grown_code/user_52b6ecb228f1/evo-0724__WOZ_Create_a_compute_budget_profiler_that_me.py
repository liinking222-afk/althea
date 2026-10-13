#!/usr/bin/env python3
"""
/autonomous-compute-profiler
Wozniak-inspired: Make every cycle count. Profile synthesis efficiency.
"""
import time
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional

class ComputeProfiler:
    def __init__(self, storage_path: str = "/tmp/althea_compute_profile.json"):
        self.storage_path = Path(storage_path)
        self.profiles: Dict[str, List[Dict]] = defaultdict(list)
        self._load()
    
    def _load(self):
        if self.storage_path.exists():
            with open(self.storage_path, 'r') as f:
                self.profiles = defaultdict(list, json.load(f))
    
    def _save(self):
        with open(self.storage_path, 'w') as f:
            json.dump(dict(self.profiles), f)
    
    def record(self, module: str, tokens_used: int, wall_time_ms: float, 
               success: bool, output_size: int = 0):
        """Record a synthesis operation's resource consumption."""
        efficiency = output_size / tokens_used if tokens_used > 0 else 0
        self.profiles[module].append({
            'timestamp': time.time(),
            'tokens': tokens_used,
            'wall_ms': wall_time_ms,
            'success': success,
            'output_bytes': output_size,
            'efficiency': efficiency
        })
        self._save()
    
    def analyze(self, module: Optional[str] = None) -> Dict:
        """Woz analysis: efficiency metrics per module."""
        if module:
            data = self.profiles.get(module, [])
        else:
            data = [item for items in self.profiles.values() for item in items]
        
        if not data:
            return {'error': 'no_data'}
        
        successes = [d for d in data if d['success']]
        total_tokens = sum(d['tokens'] for d in data)
        avg_efficiency = sum(d['efficiency'] for d in successes) / len(successes) if successes else 0
        
        return {
            'total_operations': len(data),
            'success_rate': len(successes) / len(data),
            'total_tokens_consumed': total_tokens,
            'avg_tokens_per_op': total_tokens / len(data),
            'avg_efficiency_bytes_per_token': avg_efficiency,
            'avg_wall_time_ms': sum(d['wall_ms'] for d in data) / len(data),
            'modules_tracked': len(self.profiles)
        }
    
    def report_wasteful(self, threshold: float = 0.5) -> List[str]:
        """Identify modules with success rate below threshold."""
        wasteful = []
        for module, data in self.profiles.items():
            if data:
                success_rate = sum(1 for d in data if d['success']) / len(data)
                if success_rate < threshold:
                    wasteful.append(f"{module}: {success_rate:.2%}")
        return wasteful

if __name__ == '__main__':
    profiler = ComputeProfiler()
    print(json.dumps(profiler.analyze(), indent=2))