#!/usr/bin/env python3
import sys
import json
import hashlib
from collections import defaultdict

def content_hash(obj):
    """Generate stable hash from JSON content."""
    canonical = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return hashlib.blake2s(canonical.encode(), digest_size=16).hexdigest()

def extract_fields(obj, exclude=None):
    """Extract all leaf values for delta comparison."""
    exclude = exclude or {'timestamp', 'id', 'hash'}
    leaves = []
    def recurse(o, path=''):
        if isinstance(o, dict):
            for k, v in o.items():
                if k not in exclude:
                    recurse(v, f"{path}.{k}" if path else k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                recurse(v, f"{path}[{i}]")
        else:
            leaves.append((path, o))
    recurse(obj)
    return leaves

def compress_stream(input_stream):
    """Compress JSONL memory stream with content deduplication and delta encoding."""
    seen_hashes = {}
    prev_fields = {}
    stats = defaultdict(int)
    
    for line in input_stream:
        line = line.strip()
        if not line:
            continue
        
        try:
            entry = json.loads(line)
            h = content_hash(entry)
            stats['total'] += 1
            
            if h in seen_hashes:
                # Exact duplicate - emit reference only
                print(json.dumps({'ref': h, 'first_seen': seen_hashes[h]}))
                stats['deduped'] += 1
            else:
                # New entry - check for delta encoding opportunity
                fields = extract_fields(entry)
                field_dict = dict(fields)
                
                if prev_fields:
                    delta = {k: v for k, v in field_dict.items() if prev_fields.get(k) != v}
                    removed = [k for k in prev_fields if k not in field_dict]
                    
                    if len(delta) < len(field_dict) * 0.4:  # >60% similarity
                        print(json.dumps({'hash': h, 'delta': delta, 'removed': removed}))
                        stats['delta'] += 1
                    else:
                        print(line)
                        stats['full'] += 1
                else:
                    print(line)
                    stats['full'] += 1
                
                seen_hashes[h] = stats['total']
                prev_fields = field_dict
                
        except json.JSONDecodeError:
            print(line, file=sys.stderr)
            stats['errors'] += 1
    
    print(json.dumps({'compression_stats': dict(stats)}), file=sys.stderr)

if __name__ == '__main__':
    compress_stream(sys.stdin)