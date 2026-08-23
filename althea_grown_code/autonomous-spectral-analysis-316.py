"""AUTOSYNTH — Spectral Analysis
Category: signals
Generated: 2026-08-23T07:31:56.157278+00:00
Rationale: Detected in recent dialogue: 'spectral-analysis' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

import cmath
import math


def run(signal):
    """Naive discrete Fourier transform. Works fine for the small demos
    Althea will typically need in-conversation."""
    if not signal:
        return {"ok": False, "reason": "empty_signal"}
    n = len(signal)
    spectrum = []
    for k in range(n):
        s = 0j
        for t, x in enumerate(signal):
            s += x * cmath.exp(-2j * math.pi * k * t / n)
        spectrum.append(abs(s))
    return {"ok": True, "n": n, "magnitude": spectrum}
