#!/usr/bin/env python3
"""
dormancy_detector.py - Identifies unused capabilities accumulating in the system
"""

import json
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List

DORMANCY_THRESHOLD_CYCLES = 50
STATE_FILE = Path("/tmp/althea_capability_usage.json")

class DormancyDetector:
    def __init__(self):
        self.capability_registry: Dict[str, dict] = {}
        self.load_state()
    
    def load_state(self):
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                self.capability_registry = json.load(f)
    
    def save_state(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.capability_registry, f, indent=2)
    
    def register_capability(self, name: str, module: str):
        """Register a new capability when it's added to the system"""
        if name not in self.capability_registry:
            self.capability_registry[name] = {
                'module': module,
                'added_cycle': self.current_cycle(),
                'last_used': None,
                'use_count': 0
            }
            self.save_state()
    
    def mark_used(self, name: str):
        """Mark a capability as used in current cycle"""
        if name in self.capability_registry:
            self.capability_registry[name]['last_used'] = self.current_cycle()
            self.capability_registry[name]['use_count'] += 1
            self.save_state()
    
    def current_cycle(self) -> int:
        """Derive cycle from timestamp (crude approximation)"""
        return int(time.time() / 3600)  # hourly cycles
    
    def detect_dormant(self) -> List[dict]:
        """Find capabilities that haven't been used in DORMANCY_THRESHOLD_CYCLES"""
        dormant = []
        current = self.current_cycle()
        
        for name, info in self.capability_registry.items():
            cycles_since_add = current - info['added_cycle']
            
            if info['last_used'] is None and cycles_since_add > DORMANCY_THRESHOLD_CYCLES:
                dormant.append({
                    'name': name,
                    'module': info['module'],
                    'cycles_dormant': cycles_since_add,
                    'never_used': True
                })
        
        return dormant
    
    def report(self) -> str:
        """Generate dormancy report"""
        dormant = self.detect_dormant()
        if not dormant:
            return "No dormant capabilities detected."
        
        report = f"DORMANCY ALERT: {len(dormant)} unused capabilities detected:\n"
        for cap in dormant:
            report += f"  - {cap['name']} ({cap['module']}): {cap['cycles_dormant']} cycles dormant\n"
        return report

if __name__ == "__main__":
    detector = DormancyDetector()
    print(detector.report())