#!/usr/bin/env python3
import sys
import re
from typing import Callable, Iterator

def stream_memories(input_stream=sys.stdin) -> Iterator[str]:
    """Yield memories line-by-line from input stream."""
    for line in input_stream:
        line = line.strip()
        if line:
            yield line

def grep(pattern: str) -> Callable[[Iterator[str]], Iterator[str]]:
    """Filter memories matching regex pattern."""
    regex = re.compile(pattern)
    def _filter(stream: Iterator[str]) -> Iterator[str]:
        for line in stream:
            if regex.search(line):
                yield line
    return _filter

def cut(delimiter: str, fields: list[int]) -> Callable[[Iterator[str]], Iterator[str]]:
    """Extract fields from delimited memories."""
    def _filter(stream: Iterator[str]) -> Iterator[str]:
        for line in stream:
            parts = line.split(delimiter)
            selected = [parts[i] for i in fields if i < len(parts)]
            yield delimiter.join(selected)
    return _filter

def sed(pattern: str, replacement: str) -> Callable[[Iterator[str]], Iterator[str]]:
    """Transform memories with regex substitution."""
    regex = re.compile(pattern)
    def _filter(stream: Iterator[str]) -> Iterator[str]:
        for line in stream:
            yield regex.sub(replacement, line)
    return _filter

def wc() -> Callable[[Iterator[str]], Iterator[str]]:
    """Count memories and output total."""
    def _filter(stream: Iterator[str]) -> Iterator[str]:
        count = sum(1 for _ in stream)
        yield f"{count}"
    return _filter

def pipe(*filters: Callable[[Iterator[str]], Iterator[str]]) -> Iterator[str]:
    """Compose filters left-to-right like shell pipes."""
    stream = stream_memories()
    for filter_fn in filters:
        stream = filter_fn(stream)
    return stream

def execute_pipeline(output_stream=sys.stdout, *filters):
    """Run pipeline and write to output stream."""
    for result in pipe(*filters):
        output_stream.write(result + '\n')
    output_stream.flush()

if __name__ == "__main__":
    execute_pipeline(
        sys.stdout,
        grep(r"\[EVO"),
        cut(" ", [0, 1, 2]),
        sed(r"v(\d+\.\d+\.\d+)", r"version:\1")
    )