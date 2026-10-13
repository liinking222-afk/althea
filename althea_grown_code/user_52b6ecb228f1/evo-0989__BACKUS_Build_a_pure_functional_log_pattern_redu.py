#!/usr/bin/env python3
"""Functional log pattern reducer with algebraic composition."""
from typing import Iterator, Callable, TypeVar, Tuple
from functools import reduce
from dataclasses import dataclass
from collections import defaultdict
import sys
import re

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

@dataclass(frozen=True)
class LogEvent:
    """Immutable log event as algebraic value."""
    pattern: str
    timestamp: float
    full_line: str

def parse_log_line(line: str) -> LogEvent | None:
    """Pure parser: string -> Maybe LogEvent."""
    match = re.search(r'\[AUTOSYNTH (/[a-z-]+)', line)
    if not match:
        match = re.search(r'\[EVO #\d+ \w+ v[\d.]+→[\d.]+\]', line)
        if not match:
            return None
        pattern = "EVO"
    else:
        pattern = match.group(1)
    
    return LogEvent(pattern=pattern, timestamp=0.0, full_line=line.strip())

def fold_events(acc: dict[str, int], event: LogEvent) -> dict[str, int]:
    """Associative fold operation for event aggregation."""
    return {**acc, event.pattern: acc.get(event.pattern, 0) + 1}

def compose(*fns: Callable) -> Callable:
    """Function composition: (f ∘ g)(x) = f(g(x))."""
    return lambda x: reduce(lambda v, f: f(v), fns, x)

def filter_events(predicate: Callable[[LogEvent], bool]) -> Callable[[Iterator[LogEvent]], Iterator[LogEvent]]:
    """Higher-order filter constructor."""
    return lambda events: filter(predicate, events)

def map_events(f: Callable[[LogEvent], T]) -> Callable[[Iterator[LogEvent]], Iterator[T]]:
    """Higher-order map constructor."""
    return lambda events: map(f, events)

def aggregate_stream(events: Iterator[LogEvent]) -> dict[str, int]:
    """Fold event stream into frequency map."""
    return reduce(fold_events, events, {})

def render_report(freq_map: dict[str, int]) -> str:
    """Pure renderer: data -> string."""
    lines = ["PATTERN FREQUENCY REPORT", "=" * 40]
    for pattern, count in sorted(freq_map.items(), key=lambda x: -x[1]):
        lines.append(f"{pattern:40s} {count:5d}")
    return "\n".join(lines)

# Main pipeline as pure composition
pipeline = compose(
    lambda lines: filter(None, map(parse_log_line, lines)),
    aggregate_stream,
    render_report
)

if __name__ == "__main__":
    print(pipeline(sys.stdin))