#!/usr/bin/env python3
"""
AUTOSYNTH Pattern Deduplication Filter
Compresses repetitive pattern detections into frequency summaries.
"""

import sys
import re
from collections import defaultdict
from datetime import datetime, timedelta

class PatternDeduplicator:
    def __init__(self, time_window_minutes=60):
        self.patterns = defaultdict(lambda: {
            'count': 0,
            'first_seen': None,
            'last_seen': None,
            'ids': []
        })
        self.time_window = timedelta(minutes=time_window_minutes)
    
    def parse_autosynth(self, line):
        """Extract pattern name and ID from AUTOSYNTH log line."""
        match = re.search(r'\[AUTOSYNTH (/autonomous-[\w-]+)-(\d+)\]\s+([^(]+)', line)
        if match:
            path, id_num, description = match.groups()
            pattern_key = path.rsplit('-', 1)[0]  # Remove ID suffix
            return pattern_key, id_num, description.strip()
        return None, None, None
    
    def ingest(self, line):
        """Process a log line and update pattern tracking."""
        pattern_key, id_num, description = self.parse_autosynth(line)
        if not pattern_key:
            return None
        
        now = datetime.now()
        p = self.patterns[pattern_key]
        
        if p['first_seen'] is None:
            p['first_seen'] = now
            p['description'] = description
        
        p['last_seen'] = now
        p['count'] += 1
        p['ids'].append(id_num)
        
        return pattern_key
    
    def get_summary(self):
        """Generate compressed summary of patterns."""
        summaries = []
        for pattern_key, data in sorted(self.patterns.items()):
            if data['count'] > 1:
                duration = (data['last_seen'] - data['first_seen']).total_seconds()
                summaries.append(
                    f"[DEDUPE] {pattern_key}: {data['count']}x in {duration:.0f}s "
                    f"({data['description']}) IDs:{','.join(data['ids'][:5])}"
                    + ("..." if len(data['ids']) > 5 else "")
                )
        return summaries

def main():
    deduper = PatternDeduplicator(time_window_minutes=60)
    
    for line in sys.stdin:
        line = line.strip()
        if '[AUTOSYNTH' in line:
            deduper.ingest(line)
        else:
            print(line)  # Pass through non-AUTOSYNTH lines
    
    # Emit summary at end
    for summary in deduper.get_summary():
        print(summary, file=sys.stderr)

if __name__ == '__main__':
    main()