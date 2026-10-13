#!/usr/bin/env python3
import sys
import json
from typing import Any, Callable

class StreamFilter:
    """UNIX-style composable filter for Althea module outputs."""
    
    def __init__(self):
        self.transforms: list[Callable[[Any], Any]] = []
    
    def add(self, transform: Callable[[Any], Any]) -> 'StreamFilter':
        """Chain a transformation function."""
        self.transforms.append(transform)
        return self
    
    def run(self, input_stream=sys.stdin, output_stream=sys.stdout):
        """Process stream line-by-line through transform chain."""
        for line in input_stream:
            line = line.rstrip('\n')
            try:
                data = json.loads(line) if line.startswith('{') else line
            except json.JSONDecodeError:
                data = line
            
            for transform in self.transforms:
                data = transform(data)
                if data is None:
                    break
            
            if data is not None:
                output = json.dumps(data) if isinstance(data, dict) else str(data)
                output_stream.write(output + '\n')
                output_stream.flush()

# Common composable filters
def extract_field(field: str) -> Callable:
    return lambda d: d.get(field) if isinstance(d, dict) else d

def grep(pattern: str) -> Callable:
    import re
    regex = re.compile(pattern)
    return lambda d: d if regex.search(str(d)) else None

def map_fn(fn: Callable) -> Callable:
    return fn

def limit(n: int) -> Callable:
    count = {'c': 0}
    def _limit(d):
        if count['c'] < n:
            count['c'] += 1
            return d
        return None
    return _limit

if __name__ == '__main__':
    # Example: cat modules.jsonl | ./stream_filter.py
    filter = StreamFilter()
    filter.add(extract_field('intent')).add(grep('meta')).add(limit(5))
    filter.run()