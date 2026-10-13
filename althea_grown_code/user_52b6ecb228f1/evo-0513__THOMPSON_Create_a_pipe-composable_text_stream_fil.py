#!/usr/bin/env python3
import sys
import json
from datetime import datetime
from hashlib import sha256

def stream_tagger(prefix="ALTHEA", add_hash=False, add_timestamp=False):
    """
    Read stdin line by line, emit tagged lines to stdout.
    Format: PREFIX:TIMESTAMP:HASH:original_line
    Designed to compose with grep, awk, sed in pipelines.
    """
    line_num = 0
    for line in sys.stdin:
        line_num += 1
        line = line.rstrip('\n')
        
        parts = [prefix]
        
        if add_timestamp:
            parts.append(datetime.utcnow().isoformat())
        
        if add_hash:
            h = sha256(line.encode()).hexdigest()[:8]
            parts.append(h)
        
        parts.append(str(line_num))
        parts.append(line)
        
        print(':'.join(parts))
        sys.stdout.flush()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Tag text streams for pipeline composition')
    parser.add_argument('--prefix', default='ALTHEA', help='Tag prefix')
    parser.add_argument('--hash', action='store_true', help='Add content hash')
    parser.add_argument('--timestamp', action='store_true', help='Add UTC timestamp')
    
    args = parser.parse_args()
    
    try:
        stream_tagger(prefix=args.prefix, add_hash=args.hash, add_timestamp=args.timestamp)
    except KeyboardInterrupt:
        sys.exit(0)