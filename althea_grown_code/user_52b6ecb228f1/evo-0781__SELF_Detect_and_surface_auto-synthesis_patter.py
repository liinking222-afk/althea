import json
import re
from pathlib import Path
from collections import Counter
from datetime import datetime

def detect_unfulfilled_autosynth_patterns():
    """
    Scan recent memory for AUTOSYNTH patterns that triggered multiple times
    but find no corresponding committed module in the lattice.
    Surface these as capability gaps requiring attention.
    """
    
    memory_path = Path("/tmp/althea_memory.jsonl")
    lattice_path = Path("/tmp/althea_lattice.json")
    
    # Extract pattern names from AUTOSYNTH memory entries
    autosynth_pattern = r'\[AUTOSYNTH /autonomous-([a-z\-]+)-\d+\]'
    triggered_patterns = []
    
    if memory_path.exists():
        with open(memory_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    content = entry.get('content', '')
                    matches = re.findall(autosynth_pattern, content)
                    triggered_patterns.extend(matches)
                except:
                    pass
    
    # Count pattern frequencies
    pattern_counts = Counter(triggered_patterns)
    multi_trigger_patterns = {p: c for p, c in pattern_counts.items() if c >= 2}
    
    # Load lattice to check for fulfilled patterns
    fulfilled_patterns = set()
    if lattice_path.exists():
        with open(lattice_path, 'r') as f:
            lattice = json.load(f)
            for module in lattice.get('modules', []):
                module_name = module.get('name', '').lower()
                for pattern in multi_trigger_patterns:
                    if pattern in module_name:
                        fulfilled_patterns.add(pattern)
    
    # Identify gaps
    gaps = {p: c for p, c in multi_trigger_patterns.items() 
            if p not in fulfilled_patterns}
    
    # Write gap report
    report_path = Path("/tmp/althea_capability_gaps.json")
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "unfulfilled_patterns": gaps,
        "priority": sorted(gaps.items(), key=lambda x: x[1], reverse=True)[:5]
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

if __name__ == "__main__":
    result = detect_unfulfilled_autosynth_patterns()
    print(f"Capability gaps detected: {len(result['unfulfilled_patterns'])}")
    print(f"Top priority: {result['priority'][:3]}")