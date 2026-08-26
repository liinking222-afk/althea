#!/usr/bin/env python3
"""
module_stream_filter.py - Extract and normalize module signatures from memory logs
Reads stdin, writes stdout. UNIX philosophy: do one thing well.
"""

import sys
import re
import json

def parse_memory_line(line):
    """Extract structured module data from memory log lines."""
    # Match [TYPE /path] Description pattern
    pattern = r'\[([\w]+)\s+(/[\w-]+)\]\s+([^—]+)(?:—\s+(.*))?'
    match = re.search(pattern, line)
    
    if not match:
        return None
    
    mem_type, path, description, metadata = match.groups()
    
    return {
        'type': mem_type,
        'path': path,
        'desc': description.strip(),
        'meta': metadata.strip() if metadata else '',
        'raw': line.strip()
    }

def main():
    """Read memory stream from stdin, emit JSON lines to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        parsed = parse_memory_line(line)
        if parsed:
            # Emit as JSON line for downstream pipe composition
            print(json.dumps(parsed), flush=True)
        else:
            # Pass through unparsed lines to stderr for debugging
            print(line, file=sys.stderr, flush=True)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except BrokenPipeError:
        # Graceful termination when pipe closes
        sys.exit(0)