import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class PatternConsolidator:
    def __init__(self, memory_path="./memory/autosynth"):
        self.memory_path = Path(memory_path)
        self.duplicates = defaultdict(list)
        
    def extract_signature(self, module_data):
        """Extract canonical signature from module metadata."""
        name = module_data.get('name', '').lower()
        domain = module_data.get('domain', '').lower()
        description = module_data.get('description', '').lower()
        
        # Normalize to core pattern
        pattern = re.sub(r'[^a-z0-9]', '', f"{domain}{name}")
        keywords = set(re.findall(r'\b\w{4,}\b', description))
        
        return (pattern, frozenset(keywords))
    
    def scan_modules(self):
        """Scan for duplicate auto-synthesized modules."""
        if not self.memory_path.exists():
            return {}
        
        signature_map = defaultdict(list)
        
        for module_file in self.memory_path.glob("*.json"):
            try:
                with open(module_file, 'r') as f:
                    data = json.load(f)
                    sig = self.extract_signature(data)
                    signature_map[sig].append({
                        'path': str(module_file),
                        'data': data,
                        'timestamp': data.get('created_at', '')
                    })
            except:
                continue
        
        # Identify duplicates
        for sig, modules in signature_map.items():
            if len(modules) > 1:
                self.duplicates[sig] = sorted(modules, 
    key=lambda x: x['timestamp'])
        
        return self.duplicates
    
    def consolidate(self):
        """Merge duplicates into canonical versions."""
        consolidation_log = []
        
        for sig, modules in self.duplicates.items():
            canonical = modules[-1]  # Most recent
            merged_usage = sum(m['data'].get('usage_count', 0) 
                             for m in modules)
            
            canonical['data']['usage_count'] = merged_usage
            canonical['data']['consolidated_from'] = [
                m['path'] for m in modules[:-1]
            ]
            canonical['data']['consolidation_time'] = datetime.utcnow().isoformat()
            
            # Write canonical
            with open(canonical['path'], 'w') as f:
                json.dump(canonical['data'], f, indent=2)
            
            # Archive duplicates
            for old_module in modules[:-1]:
                Path(old_module['path']).unlink(missing_ok=True)
            
            consolidation_log.append({
                'canonical': canonical['path'],
                'removed': len(modules) - 1,
                'total_usage': merged_usage
            })
        
        return consolidation_log

if __name__ == "__main__":
    consolidator = PatternConsolidator()
    duplicates = consolidator.scan_modules()
    log = consolidator.consolidate()
    print(json.dumps(log, indent=2))