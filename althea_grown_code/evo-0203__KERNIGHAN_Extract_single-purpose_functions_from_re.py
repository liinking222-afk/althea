#!/usr/bin/env python3
import re
from dataclasses import dataclass
from typing import List

@dataclass
class SinglePurposeFunction:
    name: str
    does: str
    source_module: str

def extract_verb_noun(text: str) -> tuple[str, str]:
    """Return (verb, noun) from action phrases."""
    words = text.lower().split()
    if len(words) < 2:
        return words[0] if words else "", ""
    return words[0], " ".join(words[1:])

def parse_growth_module(line: str) -> SinglePurposeFunction | None:
    """Extract one function from a GROWTH entry."""
    match = re.search(r'\[GROWTH /autonomous-([^\]]+)\] ([^(]+) \(([^)]+)\)\. (.+)', line)
    if not match:
        return None
    
    module_name = match.group(1)
    title = match.group(2).strip()
    category = match.group(3).strip()
    description = match.group(4).strip()
    
    verb, noun = extract_verb_noun(description)
    does = f"{verb} {noun}".strip()
    
    return SinglePurposeFunction(
        name=module_name.replace("-", "_"),
        does=does or description[:50],
        source_module=title
    )

def catalog_functions(memory_lines: List[str]) -> List[SinglePurposeFunction]:
    """Build catalog of single-purpose functions."""
    functions = []
    for line in memory_lines:
        func = parse_growth_module(line)
        if func:
            functions.append(func)
    return functions

def format_catalog(functions: List[SinglePurposeFunction]) -> str:
    """Format as simple text catalog."""
    lines = ["# Single-Purpose Function Catalog\n"]
    for f in functions:
        lines.append(f"{f.name}: {f.does}")
    return "\n".join(lines)

if __name__ == "__main__":
    memories = [
        "[GROWTH /autonomous-resonance-cavity-tuning] Resonance Cavity Tuning (perception). Dynamically adjusts internal feedback loops to isolate and amplify weak signals beneath dominant coherence patterns.",
        "[GROWTH /autonomous-recursion-gate-modulation] Recursion Gate Modulation (meta). Dynamically adjusts self-reference depth thresholds to permit or constrain recursive cognitive loops based on emergent",
        "[GROWTH /autonomous-resonance-field-casting] Resonance Field Casting (network). Project speculative resonance fields across concept-space to detect emergent alignments before they stabilize into patte"
    ]
    
    catalog = catalog_functions(memories)
    print(format_catalog(catalog))