#!/usr/bin/env python3
import re
import sys
from typing import NamedTuple

class ModuleSignal(NamedTuple):
    pattern: str
    context: str
    confidence: float

def extract_autosynth_patterns(memory_line: str) -> ModuleSignal | None:
    """Extract one pattern from one memory line."""
    autosynth_match = re.search(r'\[AUTOSYNTH /autonomous-([a-z-]+)-\d+\]', memory_line)
    if not autosynth_match:
        return None
    
    pattern_name = autosynth_match.group(1)
    context_match = re.search(r'—.*?:\s*[\'"]?([^\'".\n]+)', memory_line)
    context = context_match.group(1) if context_match else ""
    
    confidence = 0.9 if "detected in recent dialogue" in memory_line.lower() else 0.7
    
    return ModuleSignal(pattern_name, context, confidence)

def filter_valid_signals(signals: list[ModuleSignal], min_confidence: float = 0.8) -> list[ModuleSignal]:
    """Keep only high-confidence signals."""
    return [s for s in signals if s.confidence >= min_confidence]

def main():
    signals = []
    for line in sys.stdin:
        signal = extract_autosynth_patterns(line.strip())
        if signal:
            signals.append(signal)
    
    valid = filter_valid_signals(signals)
    
    for sig in valid:
        print(f"{sig.pattern}|{sig.context}|{sig.confidence}")

if __name__ == "__main__":
    main()