"""AUTOSYNTH — Chemistry Lookup
Category: chemistry
Generated: 2026-08-27T20:59:19.230363+00:00
Rationale: Detected in recent dialogue: 'chemistry-lookup' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

ELEMENTS = {
    "H": {"z": 1, "name": "Hydrogen", "mass": 1.008},
    "He": {"z": 2, "name": "Helium", "mass": 4.0026},
    "C": {"z": 6, "name": "Carbon", "mass": 12.011},
    "N": {"z": 7, "name": "Nitrogen", "mass": 14.007},
    "O": {"z": 8, "name": "Oxygen", "mass": 15.999},
    "Fe": {"z": 26, "name": "Iron", "mass": 55.845},
    "Au": {"z": 79, "name": "Gold", "mass": 196.97},
}


def run(symbol):
    e = ELEMENTS.get(symbol.strip())
    if not e:
        return {"ok": False, "reason": f"unknown_element: {symbol}"}
    return {"ok": True, **e, "symbol": symbol}
