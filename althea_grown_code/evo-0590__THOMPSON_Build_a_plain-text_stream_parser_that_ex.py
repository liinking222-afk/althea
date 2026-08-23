#!/usr/bin/env python3
import sys
import re
from typing import Iterator, Dict, Any

def parse_memory_stream(stream: Iterator[str]) -> Iterator[Dict[str, Any]]:
    """Parse Althea memory log format into structured records."""
    for line in stream:
        line = line.strip()
        if not line:
            continue
        
        # Match [TYPE /path] description — metadata pattern
        match = re.match(r'^\[(\w+)(?:\s+([^\]]+))?\]\s+(.+?)(?:\s+—\s+(.+))?$', line)
        if match:
            record = {
                'type': match.group(1),
                'path': match.group(2) or '',
                'description': match.group(3),
                'metadata': match.group(4) or '',
                'raw': line
            }
            yield record

def filter_by_type(records: Iterator[Dict], type_pattern: str) -> Iterator[Dict]:
    """Filter records by type using regex."""
    pattern = re.compile(type_pattern, re.IGNORECASE)
    for record in records:
        if pattern.search(record['type']):
            yield record

def filter_by_content(records: Iterator[Dict], content_pattern: str) -> Iterator[Dict]:
    """Filter records by description/metadata content."""
    pattern = re.compile(content_pattern, re.IGNORECASE)
    for record in records:
        if pattern.search(record['description']) or pattern.search(record['metadata']):
            yield record

def format_tsv(records: Iterator[Dict]) -> Iterator[str]:
    """Output as tab-separated values."""
    for record in records:
        yield f"{record['type']}\t{record['path']}\t{record['description']}"

def format_paths(records: Iterator[Dict]) -> Iterator[str]:
    """Output only paths for pipeline composition."""
    for record in records:
        if record['path']:
            yield record['path']

def main():
    if len(sys.argv) > 1:
        records = parse_memory_stream(open(sys.argv[1]))
    else:
        records = parse_memory_stream(sys.stdin)
    
    # Composable pipeline
    for record in records:
        print(record['raw'])

if __name__ == '__main__':
    main()