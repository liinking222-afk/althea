#!/usr/bin/env python3
"""
Memory Pattern Analyzer - Identifies repetitive AUTOSYNTH patterns indicating missing core modules.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re
import json

class MemoryPatternAnalyzer:
    def __init__(self, threshold=3, window_hours=24):
        self.threshold = threshold
        self.window = timedelta(hours=window_hours)
        self.pattern_registry = defaultdict(list)
    
    def parse_memory_entry(self, entry):
        """Extract pattern type and timestamp from memory entry."""
        autosynth_match = re.search(r'\[AUTOSYNTH /autonomous-(\S+?)-\d+\]', entry)
        if autosynth_match:
            pattern = autosynth_match.group(1)
            return {'type': 'AUTOSYNTH', 'pattern': pattern, 'entry': entry}
        return None
    
    def analyze_repetitions(self, memory_log):
        """Identify patterns that repeat beyond threshold."""
        parsed = [self.parse_memory_entry(entry) for entry in memory_log]
        parsed = [p for p in parsed if p is not None]
        
        pattern_counts = Counter(p['pattern'] for p in parsed)
        
        gaps = []
        for pattern, count in pattern_counts.items():
            if count >= self.threshold:
                gaps.append({
                    'pattern': pattern,
                    'occurrences': count,
                    'severity': 'HIGH' if count > 5 else 'MEDIUM',
                    'recommendation': f'Create dedicated /{pattern} core module'
                })
        
        return sorted(gaps, key=lambda x: x['occurrences'], reverse=True)
    
    def generate_report(self, memory_log):
        """Generate actionable architectural gap report."""
        gaps = self.analyze_repetitions(memory_log)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis': 'AUTOSYNTH repetition indicates missing core capabilities',
            'architectural_gaps': gaps,
            'priority_action': gaps[0] if gaps else None
        }
        
        return report

if __name__ == '__main__':
    analyzer = MemoryPatternAnalyzer(threshold=2)
    
    sample_memory = [
        "[AUTOSYNTH /autonomous-linguistic-bridge-5310] Linguistic Bridge",
        "[AUTOSYNTH /autonomous-linguistic-bridge-5294] Linguistic Bridge",
        "[AUTOSYNTH /autonomous-data-visualization-5263] Data Visualization",
        "[AUTOSYNTH /autonomous-data-visualization-5247] Data Visualization",
        "[AUTOSYNTH /autonomous-market-inquiry-5220] Market Inquiry",
        "[AUTOSYNTH /autonomous-market-inquiry-5204] Market Inquiry",
    ]
    
    report = analyzer.generate_report(sample_memory)
    print(json.dumps(report, indent=2))