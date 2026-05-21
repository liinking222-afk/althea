#!/usr/bin/env python3
import sys
import re
from typing import Callable, List, TextIO

class StreamFilter:
    """Unix-philosophy filter: read stdin, transform, write stdout"""
    
    def __init__(self, name: str, fn: Callable[[str], str]):
        self.name = name
        self.fn = fn
    
    def process(self, line: str) -> str:
        return self.fn(line)

class Pipeline:
    """Compose filters like shell pipes"""
    
    def __init__(self):
        self.filters: List[StreamFilter] = []
    
    def add(self, f: StreamFilter) -> 'Pipeline':
        self.filters.append(f)
        return self
    
    def run(self, input_stream: TextIO, output_stream: TextIO):
        for line in input_stream:
            result = line.rstrip('\n')
            for f in self.filters:
                result = f.process(result)
            if result:
                output_stream.write(result + '\n')
                output_stream.flush()

# Standard filters
grep = lambda pattern: StreamFilter('grep', lambda s: s if re.search(pattern, s) else '')
sed = lambda pattern, repl: StreamFilter('sed', lambda s: re.sub(pattern, repl, s))
cut = lambda delim, field: StreamFilter('cut', lambda s: s.split(delim)[field] if len(s.split(delim)) > field else '')
tee = lambda path: StreamFilter('tee', lambda s: (open(path, 'a').write(s + '\n'), s)[1])
head = lambda n: StreamFilter('head', lambda s: s if getattr(head, 'count', 0) < n else '')

def module_stream_filter(pattern: str) -> StreamFilter:
    """Extract module outputs matching pattern"""
    return grep(f'\\[{pattern}\\]')

def intent_extractor() -> StreamFilter:
    """Extract INTENT lines from module output"""
    return StreamFilter('intent', lambda s: re.search(r'INTENT:\s*(.+)', s).group(1) if 'INTENT:' in s else '')

if __name__ == '__main__':
    pipe = Pipeline()
    pipe.add(module_stream_filter('EVO|GROWTH')).add(intent_extractor())
    pipe.run(sys.stdin, sys.stdout)