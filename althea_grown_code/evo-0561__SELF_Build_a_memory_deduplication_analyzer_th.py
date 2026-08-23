import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

class MemoryDeduplicator:
    """Analyzes memory streams for redundant patterns and proposes consolidation."""
    
    def __init__(self):
        self.pattern_signatures = defaultdict(list)
        self.consolidation_candidates = []
    
    def parse_memory_entry(self, entry: str) -> Tuple[str, str, str]:
        """Extract type, path, and description from memory entry."""
        type_match = re.search(r'\[(AUTOSYNTH|GROWTH|EVO)\s+([^\]]+)\]', entry)
        desc_match = re.search(r'\]\s+(.+?)(?:\s+—|$)', entry)
        
        if not type_match:
            return None, None, None
        
        mem_type = type_match.group(1)
        path = type_match.group(2).strip()
        description = desc_match.group(1).strip() if desc_match else ""
        
        return mem_type, path, description
    
    def compute_signature(self, mem_type: str, description: str) -> str:
        """Create semantic signature from memory entry."""
        core = re.sub(r'\(.*?\)', '', description).strip()
        core = re.sub(r'[^\w\s-]', '', core.lower())
        return f"{mem_type}:{core}"
    
    def analyze(self, memory_log: List[str]) -> Dict:
        """Identify duplicate patterns in memory."""
        for entry in memory_log:
            mem_type, path, description = self.parse_memory_entry(entry)
            if not mem_type:
                continue
            
            signature = self.compute_signature(mem_type, description)
            self.pattern_signatures[signature].append({
                'path': path,
                'description': description,
                'entry': entry
            })
        
        # Find duplicates
        for signature, instances in self.pattern_signatures.items():
            if len(instances) >= 2:
                self.consolidation_candidates.append({
                    'signature': signature,
                    'count': len(instances),
                    'instances': instances
                })
        
        return {
            'total_memories': len(memory_log),
            'unique_patterns': len(self.pattern_signatures),
            'duplicate_patterns': len(self.consolidation_candidates),
            'redundancy_ratio': len(self.consolidation_candidates) / max(len(self.pattern_signatures), 1),
            'candidates': sorted(self.consolidation_candidates, key=lambda x: x['count'], reverse=True)
        }
    
    def generate_consolidation_plan(self) -> List[str]:
        """Propose specific consolidation actions."""
        plans = []
        for candidate in self.consolidation_candidates:
            plans.append(f"CONSOLIDATE {candidate['count']} instances of '{candidate['signature']}' into single stable module")
        return plans

def deduplicate_memory_stream(memory_entries: List[str]) -> Dict:
    """Main entry point for memory deduplication analysis."""
    dedup = MemoryDeduplicator()
    return dedup.analyze(memory_entries)