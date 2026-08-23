#!/usr/bin/env python3
import hashlib
import json
import re
from collections import defaultdict
from typing import Dict, List, Tuple

class ModuleCompressor:
    """Woz-style constraint optimizer: make every byte count in module storage."""
    
    def __init__(self):
        self.pattern_dict: Dict[str, int] = {}
        self.reverse_dict: Dict[int, str] = {}
        self.next_id = 0
        self.compression_stats = defaultdict(int)
    
    def fingerprint(self, module_text: str) -> str:
        """Extract semantic fingerprint from module description."""
        normalized = re.sub(r'\s+', ' ', module_text.lower().strip())
        normalized = re.sub(r'\d{4}', 'NNNN', normalized)  # Collapse IDs
        return hashlib.blake2s(normalized.encode(), digest_size=8).hexdigest()
    
    def compress_module(self, module_record: str) -> Tuple[int, bool]:
        """Return (pattern_id, is_new). Hardware mindset: reuse circuits."""
        fp = self.fingerprint(module_record)
        
        if fp in self.pattern_dict:
            pid = self.pattern_dict[fp]
            self.compression_stats['dedup_hits'] += 1
            return (pid, False)
        
        pid = self.next_id
        self.pattern_dict[fp] = pid
        self.reverse_dict[pid] = module_record
        self.next_id += 1
        self.compression_stats['unique_patterns'] += 1
        return (pid, True)
    
    def decompress(self, pattern_id: int) -> str:
        """Retrieve original from compressed form."""
        return self.reverse_dict.get(pattern_id, "")
    
    def efficiency_ratio(self) -> float:
        """Calculate space savings. Elegance metric."""
        total = self.compression_stats['dedup_hits'] + self.compression_stats['unique_patterns']
        if total == 0:
            return 0.0
        return self.compression_stats['dedup_hits'] / total
    
    def export_manifest(self) -> str:
        """Compact JSON representation for persistence."""
        return json.dumps({
            'patterns': self.reverse_dict,
            'stats': dict(self.compression_stats),
            'efficiency': round(self.efficiency_ratio(), 3)
        }, separators=(',', ':'))

if __name__ == '__main__':
    comp = ModuleCompressor()
    
    # Simulate AUTOSYNTH duplicates from memory
    test_modules = [
        "[AUTOSYNTH /autonomous-chemistry-lookup-1173] Chemistry Lookup",
        "[AUTOSYNTH /autonomous-chemistry-lookup-1103] Chemistry Lookup",
        "[AUTOSYNTH /autonomous-transfer-learning-1157] Transfer Learning",
        "[AUTOSYNTH /autonomous-transfer-learning-1119] Transfer Learning"
    ]
    
    for mod in test_modules:
        pid, new = comp.compress_module(mod)
        print(f"{'NEW' if new else 'DUP'} -> ID:{pid}")
    
    print(f"\nEfficiency: {comp.efficiency_ratio():.1%} space saved")
    print(comp.export_manifest())