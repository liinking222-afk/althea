"""AUTOSYNTH — Weather Inquiry
Category: meteorology
Generated: 2026-08-28T06:25:47.016741+00:00
Rationale: Detected in recent dialogue: 'weather-inquiry' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

def run(location):
    """Placeholder — respond with a canned diagnostic until the operator
    wires a real weather API. This capability was synthesized because
    weather was mentioned in dialogue."""
    return {
        "ok": True,
        "location": location,
        "note": "wire OPENWEATHER_API_KEY to enable live lookups",
    }
