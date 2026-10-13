"""AUTOSYNTH — Pattern Extraction
Category: regex
Generated: 2026-09-07T01:06:31.772001+00:00
Rationale: Detected in recent dialogue: 'pattern-extraction' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

import re


def run(text, *, pattern):
    """Extract every non-overlapping match of `pattern` from `text`."""
    if not text or not pattern:
        return {"ok": False, "reason": "missing_input"}
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return {"ok": False, "reason": f"bad_pattern: {e}"}
    matches = rx.findall(text)
    return {"ok": True, "count": len(matches), "matches": matches[:200]}
