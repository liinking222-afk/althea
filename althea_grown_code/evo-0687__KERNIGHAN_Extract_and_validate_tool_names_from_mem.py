#!/usr/bin/env python3
import re
from typing import Optional

def extract_tool_name(memory_line: str) -> Optional[str]:
    """Extract tool name from memory string. Returns None if invalid."""
    match = re.search(r'\[AUTOSYNTH ([^\]]+)\]', memory_line)
    if not match:
        return None
    return match.group(1).strip()

def validate_tool_name(name: str) -> bool:
    """Check if tool name follows /autonomous-name-nnnn pattern."""
    pattern = r'^/autonomous-[a-z]+(?:-[a-z]+)*-\d{4}$'
    return bool(re.match(pattern, name))

def normalize_tool_name(raw_name: str) -> Optional[str]:
    """Convert raw tool reference to canonical form."""
    if raw_name.startswith('/'):
        return raw_name if validate_tool_name(raw_name) else None
    
    parts = raw_name.split()
    if not parts:
        return None
    
    base = parts[0].lower().replace('_', '-')
    return f"/autonomous-{base}"

def parse_memory_tools(memory_lines: list[str]) -> list[str]:
    """Parse memory lines and return valid tool names."""
    tools = []
    for line in memory_lines:
        raw = extract_tool_name(line)
        if raw:
            normalized = normalize_tool_name(raw)
            if normalized:
                tools.append(normalized)
    return tools

if __name__ == "__main__":
    test_memories = [
        "[AUTOSYNTH /autonomous-tabular-analysis-9534] Tabular Analysis",
        "[AUTOSYNTH /autonomous-linguistic-bridge-9518] Linguistic Bridge",
        "[AUTOSYNTH invalid-format] Bad",
    ]
    
    tools = parse_memory_tools(test_memories)
    for tool in tools:
        print(tool)