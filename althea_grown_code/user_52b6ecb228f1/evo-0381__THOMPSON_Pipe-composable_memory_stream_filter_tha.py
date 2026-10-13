#!/usr/bin/env python3
import sys
import json
from collections import Counter, defaultdict

def parse_memory_stream():
    """Read JSONL memory entries from stdin, yield parsed objects."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue

def extract_fields(entries):
    """Extract field statistics from memory entries."""
    types = Counter()
    archetypes = Counter()
    tags = Counter()
    word_freq = Counter()
    
    for entry in entries:
        entry_type = entry.get('type', 'UNKNOWN')
        types[entry_type] += 1
        
        if 'archetype' in entry:
            archetypes[entry.get('archetype')] += 1
        
        if 'tags' in entry and isinstance(entry['tags'], list):
            tags.update(entry['tags'])
        
        content = entry.get('content', '') or entry.get('text', '')
        if content:
            words = content.lower().split()
            word_freq.update(w for w in words if len(w) > 3)
    
    return types, archetypes, tags, word_freq

def main():
    entries = list(parse_memory_stream())
    
    if not entries:
        print("# NO MEMORY STREAM DATA", file=sys.stderr)
        sys.exit(1)
    
    types, archetypes, tags, words = extract_fields(entries)
    
    print(f"TOTAL_ENTRIES\t{len(entries)}")
    print()
    
    print("TYPE_DISTRIBUTION")
    for typ, count in types.most_common():
        print(f"{typ}\t{count}")
    print()
    
    if archetypes:
        print("ARCHETYPE_FREQUENCY")
        for arch, count in archetypes.most_common(10):
            print(f"{arch}\t{count}")
        print()
    
    if tags:
        print("TAG_FREQUENCY")
        for tag, count in tags.most_common(15):
            print(f"{tag}\t{count}")
        print()
    
    print("TOP_CONCEPTS")
    for word, count in words.most_common(20):
        print(f"{word}\t{count}")

if __name__ == '__main__':
    main()