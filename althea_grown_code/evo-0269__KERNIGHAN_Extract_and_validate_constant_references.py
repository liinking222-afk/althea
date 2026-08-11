#!/usr/bin/env python3
import re
from typing import Optional, Dict

def extract_constant(text: str) -> Optional[Dict[str, str]]:
    """Parse 'favorite constant is X' pattern."""
    match = re.search(r"favorite constant is ([A-Za-z'\s]+)", text, re.IGNORECASE)
    if not match:
        return None
    return {"name": match.group(1).strip()}

def validate_constant(name: str) -> bool:
    """Check if constant name maps to known mathematical entity."""
    known = {
        "euler's number e": "e",
        "pi": "π",
        "golden ratio": "φ",
        "imaginary unit": "i",
        "planck constant": "h"
    }
    return name.lower() in known

def remember_constant(memory_lines: list) -> Optional[str]:
    """Scan memory for last declared favorite constant."""
    for line in reversed(memory_lines):
        const = extract_constant(line)
        if const and validate_constant(const["name"]):
            return const["name"]
    return None

def format_constant_memory(name: str) -> str:
    """Emit constant as retrievable token."""
    return f"CONSTANT:{name.upper()}"

if __name__ == "__main__":
    memory = [
        "what did I just tell you was my favorite constant?",
        "remember this: my favorite constant is Euler's number e",
        "Yes"
    ]
    
    constant = remember_constant(memory)
    if constant:
        print(format_constant_memory(constant))