#!/usr/bin/env python3
import sys
import json
import re
from datetime import datetime

def parse_memory_line(line):
    """Extract structured data from memory log lines using simple regex."""
    line = line.strip()
    if not line:
        return None
    
    # Pattern: [TYPE /path-or-id] Content — metadata
    match = re.match(r'^\[([A-Z]+)\s+([^\]]+)\]\s+(.+?)(?:\s+—\s+(.+))?$', line)
    if not match:
        return None
    
    record_type, path, content, metadata = match.groups()
    
    # Extract version changes if present
    version_match = re.search(r'v?([\d.]+)→([\d.]+)', path)
    
    return {
        'type': record_type,
        'path': path.strip(),
        'content': content.strip(),
        'metadata': metadata.strip() if metadata else '',
        'from_version': version_match.group(1) if version_match else None,
        'to_version': version_match.group(2) if version_match else None,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

def main():
    """Read stdin line by line, emit NDJSON to stdout."""
    for line in sys.stdin:
        record = parse_memory_line(line)
        if record:
            print(json.dumps(record, separators=(',', ':')))
            sys.stdout.flush()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except BrokenPipeError:
        sys.exit(0)