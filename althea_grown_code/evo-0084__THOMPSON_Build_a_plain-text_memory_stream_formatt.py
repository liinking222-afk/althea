#!/usr/bin/env python3
import sys
import json
from datetime import datetime

def format_memory_line(mem):
    """Format memory as pipe-delimited plain text for shell composition."""
    timestamp = datetime.now().isoformat()
    
    if isinstance(mem, dict):
        mem_type = mem.get('type', 'UNKNOWN')
        source = mem.get('source', 'unknown')
        size = mem.get('size', '')
        tab = mem.get('tab', '')
        online = mem.get('online', '')
        count = mem.get('memory_count', '')
        bytes_val = mem.get('bytes', '')
        
        parts = [
            timestamp,
            mem_type,
            source,
            str(size),
            str(tab),
            str(online),
            str(count),
            str(bytes_val)
        ]
    elif isinstance(mem, str):
        parts = [timestamp, 'RAW', 'stdin', mem.strip()]
    else:
        parts = [timestamp, 'RAW', 'stdin', str(mem)]
    
    return '|'.join(parts)

def main():
    """Read memories from stdin (JSON lines or raw), output pipe-delimited."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            mem = json.loads(line)
        except json.JSONDecodeError:
            mem = line
        
        print(format_memory_line(mem))
        sys.stdout.flush()

if __name__ == '__main__':
    main()