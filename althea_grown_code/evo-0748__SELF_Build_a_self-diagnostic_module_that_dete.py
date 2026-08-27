#!/usr/bin/env python3
import sys
import json
from collections import defaultdict, Counter
from datetime import datetime

def analyze_repetition_patterns(memories):
    """Detect repetitive AUTOSYNTH patterns suggesting need for abstraction."""
    autosynth_patterns = defaultdict(list)
    
    for mem in memories:
        if mem.get('type') == 'AUTOSYNTH':
            module_name = mem.get('module', '').split('-')[-1]
            base_pattern = '-'.join(mem.get('module', '').split('-')[:-1])
            autosynth_patterns[base_pattern].append({
                'timestamp': mem.get('timestamp', ''),
                'full_module': mem.get('module', ''),
                'category': mem.get('category', '')
            })
    
    insights = []
    for pattern, occurrences in autosynth_patterns.items():
        if len(occurrences) >= 3:
            frequency = len(occurrences)
            categories = set(o['category'] for o in occurrences)
            insights.append({
                'pattern': pattern,
                'frequency': frequency,
                'categories': list(categories),
                'recommendation': f'Consider promoting {pattern} from AUTOSYNTH to permanent module',
                'severity': 'high' if frequency >= 5 else 'medium'
            })
    
    return sorted(insights, key=lambda x: x['frequency'], reverse=True)

def main():
    try:
        data = json.load(sys.stdin)
        memories = data if isinstance(data, list) else data.get('memories', [])
        
        patterns = analyze_repetition_patterns(memories)
        
        output = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'analysis': 'repetition_pattern_detection',
            'abstraction_opportunities': patterns,
            'total_opportunities': len(patterns)
        }
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()