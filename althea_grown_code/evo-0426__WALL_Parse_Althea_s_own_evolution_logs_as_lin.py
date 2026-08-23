#!/usr/bin/env python3
import re
import sys
import json
from typing import Iterator, Dict, Any

def parse_evolution_entry(line: str) -> Dict[str, Any]:
    """Duck-typed parser: handles multiple evolution log formats pragmatically."""
    line = line.strip()
    if not line:
        return None
    
    # [EVO #N ARCHETYPE vX→vY] description — details
    evo_match = re.match(r'\[EVO\s+#(\d+)\s+(\w+)\s+v([\d.]+)→v([\d.]+)\]\s+(.+?)(?:\s+—\s+(.+))?$', line)
    if evo_match:
        return {
            "type": "evolution",
            "id": int(evo_match.group(1)),
            "archetype": evo_match.group(2),
            "version_from": evo_match.group(3),
            "version_to": evo_match.group(4),
            "description": evo_match.group(5),
            "details": evo_match.group(6) or ""
        }
    
    # [GROWTH /path] Name (category). Description — rationale
    growth_match = re.match(r'\[GROWTH\s+(/[\w\-/]+)\]\s+(.+?)\s+\((.+?)\)\.\s+(.+?)(?:\s+—\s+(.+))?$', line)
    if growth_match:
        return {
            "type": "growth",
            "path": growth_match.group(1),
            "name": growth_match.group(2),
            "category": growth_match.group(3),
            "description": growth_match.group(4),
            "rationale": growth_match.group(5) or ""
        }
    
    # [AUTOSYNTH /path] Name (tech). Description — rationale
    synth_match = re.match(r'\[AUTOSYNTH\s+(/[\w\-/]+)\]\s+(.+?)\s+\((.+?)\)\.\s+(.+?)(?:\s+—\s+(.+))?$', line)
    if synth_match:
        return {
            "type": "autosynth",
            "path": synth_match.group(1),
            "name": synth_match.group(2),
            "technology": synth_match.group(3),
            "description": synth_match.group(4),
            "rationale": synth_match.group(5) or ""
        }
    
    # Fallback: raw text
    return {"type": "raw", "content": line}

def stream_parse(input_stream: Iterator[str]) -> Iterator[str]:
    """Stream processor: one line in, one JSON out. UNIX-friendly."""
    for line in input_stream:
        parsed = parse_evolution_entry(line)
        if parsed:
            yield json.dumps(parsed, separators=(',', ':'))

if __name__ == "__main__":
    for json_line in stream_parse(sys.stdin):
        print(json_line)