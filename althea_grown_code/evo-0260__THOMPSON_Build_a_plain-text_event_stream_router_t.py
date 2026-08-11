#!/usr/bin/env python3
import sys
import re
from collections import deque
from typing import Callable, Iterator

class StreamRouter:
    """UNIX-philosophy event router: plain text in, plain text out."""
    
    def __init__(self):
        self.filters: list[Callable[[str], Iterator[str]]] = []
    
    def pipe(self, filter_fn: Callable[[str], Iterator[str]]) -> 'StreamRouter':
        """Chain filters like shell pipelines."""
        self.filters.append(filter_fn)
        return self
    
    def process(self, input_stream: Iterator[str]) -> Iterator[str]:
        """Execute filter chain on input stream."""
        stream = input_stream
        for filter_fn in self.filters:
            stream = (line for event in stream for line in filter_fn(event))
        return stream

def grep(pattern: str) -> Callable[[str], Iterator[str]]:
    """Filter events matching regex pattern."""
    regex = re.compile(pattern)
    def _filter(line: str) -> Iterator[str]:
        if regex.search(line):
            yield line
    return _filter

def sed(pattern: str, replacement: str) -> Callable[[str], Iterator[str]]:
    """Transform events via regex substitution."""
    regex = re.compile(pattern)
    def _filter(line: str) -> Iterator[str]:
        yield regex.sub(replacement, line)
    return _filter

def tee(filepath: str) -> Callable[[str], Iterator[str]]:
    """Write to file while passing through."""
    def _filter(line: str) -> Iterator[str]:
        with open(filepath, 'a') as f:
            f.write(line + '\n')
        yield line
    return _filter

def head(n: int) -> Callable[[str], Iterator[str]]:
    """Take first n events."""
    count = {'val': 0}
    def _filter(line: str) -> Iterator[str]:
        if count['val'] < n:
            count['val'] += 1
            yield line
    return _filter

def tail(n: int) -> Callable[[str], Iterator[str]]:
    """Keep last n events in buffer."""
    buffer = deque(maxlen=n)
    def _filter(line: str) -> Iterator[str]:
        buffer.append(line)
        for item in buffer:
            yield item
        buffer.clear()
    return _filter

if __name__ == '__main__':
    router = StreamRouter()
    router.pipe(grep(r'\[EVO')).pipe(sed(r'v(\d+\.\d+\.\d+)', r'version:\1'))
    
    events = sys.stdin if not sys.stdin.isatty() else iter([
        "[EVO #259 KAY v1.22.5→1.22.6] Hot-swap kernel",
        "[GROWTH /local-prune] Decay nodes",
        "[EVO #258 KERNIGHAN v1.22.4→1.22.5] Self-improvement"
    ])
    
    for output in router.process(events):
        print(output)