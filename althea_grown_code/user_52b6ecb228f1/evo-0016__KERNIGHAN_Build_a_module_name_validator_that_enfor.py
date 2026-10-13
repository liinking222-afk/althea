#!/usr/bin/env python3
"""name_clarity.py - Enforce Kernighan clarity in module names."""

import re
import sys

VAGUE_WORDS = {
    "process", "handle", "manage", "do", "perform", "execute",
    "system", "data", "info", "stuff", "thing", "util", "helper"
}

ACTION_VERBS = {
    "parse", "validate", "route", "cache", "profile", "compose",
    "map", "filter", "reduce", "transform", "encode", "decode",
    "read", "write", "send", "receive", "open", "close",
    "create", "delete", "update", "find", "search", "sort",
    "lock", "unlock", "start", "stop", "emit", "listen"
}

def count_verbs(name):
    """Count action verbs in name."""
    words = re.findall(r'[a-z]+', name.lower())
    return sum(1 for w in words if w in ACTION_VERBS)

def has_vague_word(name):
    """Check for vague words."""
    words = re.findall(r'[a-z]+', name.lower())
    return any(w in VAGUE_WORDS for w in words)

def validate_name(name):
    """Return True if name is clear, False otherwise."""
    if not name or len(name) < 3:
        return False
    
    verb_count = count_verbs(name)
    
    if verb_count != 1:
        return False
    
    if has_vague_word(name):
        return False
    
    return True

def main():
    """Read module name, validate, exit 0 if clear, 1 if vague."""
    if len(sys.argv) != 2:
        print("usage: name_clarity.py <module_name>", file=sys.stderr)
        sys.exit(2)
    
    name = sys.argv[1]
    
    if validate_name(name):
        print(f"CLEAR: {name}")
        sys.exit(0)
    else:
        verb_count = count_verbs(name)
        if verb_count == 0:
            print(f"REJECT: {name} - no action verb", file=sys.stderr)
        elif verb_count > 1:
            print(f"REJECT: {name} - multiple verbs (does {verb_count} things)", file=sys.stderr)
        elif has_vague_word(name):
            print(f"REJECT: {name} - contains vague word", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()