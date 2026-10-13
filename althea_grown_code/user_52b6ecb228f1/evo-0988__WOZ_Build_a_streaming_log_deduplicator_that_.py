#!/usr/bin/env python3
import sys
import re
from collections import defaultdict
from datetime import datetime, timedelta

class StreamingDeduplicator:
    def __init__(self, window_seconds=300):
        self.window = timedelta(seconds=window_seconds)
        self.patterns = defaultdict(lambda: {"count": 0, "first": None, "last": None})
        self.last_flush = datetime.now()
        
    def parse_line(self, line):
        match = re.search(r'\[AUTOSYNTH\s+(/[\w-]+)\]', line)
        if not match:
            return None
        return match.group(1)
    
    def ingest(self, line, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
        
        pattern = self.parse_line(line)
        if pattern:
            entry = self.patterns[pattern]
            if entry["first"] is None:
                entry["first"] = timestamp
            entry["last"] = timestamp
            entry["count"] += 1
            return True
        return False
    
    def should_flush(self, now=None):
        if now is None:
            now = datetime.now()
        return (now - self.last_flush) >= self.window
    
    def flush(self, now=None):
        if now is None:
            now = datetime.now()
        
        output = []
        for pattern, data in sorted(self.patterns.items()):
            if data["count"] > 1:
                duration = (data["last"] - data["first"]).total_seconds()
                output.append(f"{pattern}\t{data['count']}\t{duration:.1f}s")
            elif data["count"] == 1:
                output.append(f"{pattern}\t1\tsingleton")
        
        self.patterns.clear()
        self.last_flush = now
        return output

def main():
    dedup = StreamingDeduplicator(window_seconds=300)
    
    for line in sys.stdin:
        line = line.rstrip()
        dedup.ingest(line)
        
        if dedup.should_flush():
            for summary in dedup.flush():
                print(summary, flush=True)
    
    for summary in dedup.flush():
        print(summary, flush=True)

if __name__ == "__main__":
    main()