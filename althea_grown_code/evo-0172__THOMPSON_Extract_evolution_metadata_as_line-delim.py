#!/usr/bin/env python3
import sys
import json
import re
from typing import TextIO

def parse_evo_line(line: str) -> dict | None:
    """Parse evolution log line into structured record."""
    match = re.match(r'\[EVO #(\d+) (\w+) v([\d.]+)→v([\d.]+)\] (.+?) — (.+)', line)
    if not match:
        return None
    
    evo_id, archetype, from_v, to_v, title, rationale = match.groups()
    
    return {
        "type": "evolution",
        "id": int(evo_id),
        "archetype": archetype,
        "version_from": from_v,
        "version_to": to_v,
        "title": title.strip(),
        "rationale": rationale.strip()
    }

def parse_growth_line(line: str) -> dict | None:
    """Parse growth module line into structured record."""
    match = re.match(r'\[GROWTH (/[\w-]+)\] ([^(]+)\(([^)]+)\)\. (.+?)(?:— (.+))?$', line)
    if not match:
        return None
    
    path, name, category, description = match.groups()[:4]
    rationale = match.groups()[4] or ""
    
    return {
        "type": "growth",
        "path": path,
        "name": name.strip(),
        "category": category.strip(),
        "description": description.strip(),
        "rationale": rationale.strip()
    }

def stream_parse(input_stream: TextIO) -> None:
    """Stream parse input, emit one JSON object per line."""
    for line in input_stream:
        line = line.strip()
        if not line:
            continue
        
        record = parse_evo_line(line) or parse_growth_line(line)
        if record:
            print(json.dumps(record, separators=(',', ':')))

if __name__ == "__main__":
    stream_parse(sys.stdin)