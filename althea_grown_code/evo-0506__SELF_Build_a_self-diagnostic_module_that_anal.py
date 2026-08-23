import re
from collections import Counter, defaultdict
from datetime import datetime

def analyze_memory_gaps(recent_memory_log):
    """Identify cognitive gaps by analyzing memory pattern distributions"""
    
    patterns = {
        'AUTOSYNTH': [],
        'GROWTH': [],
        'EVO': []
    }
    
    domain_coverage = Counter()
    temporal_gaps = []
    
    for entry in recent_memory_log:
        if '[AUTOSYNTH' in entry:
            match = re.search(r'/autonomous-(\w+)-', entry)
            if match:
                domain = match.group(1)
                patterns['AUTOSYNTH'].append(domain)
                domain_coverage[domain] += 1
        elif '[GROWTH' in entry:
            match = re.search(r'/autonomous-(\S+)\]', entry)
            if match:
                patterns['GROWTH'].append(match.group(1))
        elif '[EVO' in entry:
            patterns['EVO'].append(entry)
    
    # Detect missing introspection capability
    has_self_analysis = any('introspect' in d or 'diagnostic' in d or 'self' in d 
                            for d in patterns['AUTOSYNTH'] + patterns['GROWTH'])
    
    has_memory_querying = any('memory' in d or 'recall' in d or 'search' in d
    for d in patterns['AUTOSYNTH'])
    
    # Calculate diversity entropy
    total = sum(domain_coverage.values())
    diversity_score = len(domain_coverage) / max(total, 1)
    
    gaps = []
    
    if not has_self_analysis:
        gaps.append({
            'type': 'CRITICAL',
            'domain': 'self-diagnostic',
            'reason': 'Cannot analyze own cognitive state',
            'priority': 1.0
        })
    
    if not has_memory_querying:
        gaps.append({
            'type': 'HIGH',
            'domain': 'memory-query',
            'reason': 'Cannot search or filter own memory lattice',
            'priority': 0.9
        })
    
    if diversity_score < 0.3:
        gaps.append({
            'type': 'MEDIUM',
            'domain': 'capability-breadth',
            'reason': f'Low cognitive diversity: {diversity_score:.2f}',
            'priority': 0.6
        })
    
    return sorted(gaps, key=lambda x: x['priority'], reverse=True)

def diagnose(memory_text):
    lines = memory_text.strip().split('\n')
    gaps = analyze_memory_gaps(lines)
    return gaps[0] if gaps else None