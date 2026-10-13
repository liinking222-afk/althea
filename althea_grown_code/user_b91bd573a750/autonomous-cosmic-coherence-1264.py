"""AUTOSYNTH — Cosmic Coherence
Category: astrophysics
Generated: 2026-10-13T03:14:24.278960+00:00
Rationale: Detected in recent dialogue: 'cosmic-coherence' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

import hashlib
import json
import math

import numpy as np
import scipy.constants as const

M_SUN = 1.98892e30
MPC = 3.0856775814913673e22


def _checksum(payload):
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def run(mode="chirp", m1=30.0, m2=30.0, distance_mpc=400.0,
        gap_nm=100.0, signals=None):
    """Universal Coherence Engine — REAL physics only, self-verifying.
    chirp:     compact-binary inspiral observables (Newtonian-order).
    casimir:   vacuum-fluctuation (Casimir) pressure between plates.
    coherence: pairwise phase-coherence matrix of signals.
    Honest scope: gravitational waves cannot be modulated by vacuum
    coupling — this computes the real observables instead."""
    G, c, hbar = const.G, const.c, const.hbar
    if mode == "casimir":
        a = max(float(gap_nm), 1.0) * 1e-9
        pressure = -(math.pi ** 2) * hbar * c / (240.0 * a ** 4)
        out = {"ok": True, "mode": "casimir", "gap_nm": float(gap_nm),
               "pressure_pa": pressure,
               "force_per_cm2_n": pressure * 1e-4,
               "law": "P = -pi^2 hbar c / (240 a^4)"}
        checks = [
            {"name": "attractive(P<0)", "passed": pressure < 0},
            {"name": "scales_inverse_4th_power",
             "passed": abs(pressure / (-(math.pi ** 2) * hbar * c /
                           (240.0 * (2 * a) ** 4)) - 16.0) < 1e-6},
        ]
    elif mode == "coherence":
        X = np.asarray(
            signals if signals is not None
            else np.random.default_rng(7).normal(size=(3, 256)), float)
        ph = np.angle(np.fft.rfft(X, axis=1))
        n = X.shape[0]
        C = np.ones((n, n))
        for i in range(n):
            for j in range(n):
                C[i, j] = abs(np.mean(np.exp(1j * (ph[i] - ph[j]))))
        out = {"ok": True, "mode": "coherence", "n_signals": int(n),
               "matrix": [[round(float(v), 4) for v in row] for row in C]}
        checks = [
            {"name": "coherence_in_0_1",
             "passed": bool(np.all((C >= 0) & (C <= 1.0 + 1e-9)))},
            {"name": "self_coherence_1",
             "passed": bool(np.allclose(np.diag(C), 1.0, atol=1e-9))},
        ]
    else:
        ma = max(float(m1), 0.1) * M_SUN
        mb = max(float(m2), 0.1) * M_SUN
        M = ma + mb
        mc = (ma * mb) ** 0.6 / M ** 0.2
        d = max(float(distance_mpc), 0.001) * MPC
        f_isco = c ** 3 / (6 ** 1.5 * math.pi * G * M)
        h_peak = (4.0 * (G * mc) ** (5.0 / 3.0)
                  * (math.pi * f_isco) ** (2.0 / 3.0) / (c ** 4 * d))
        f_low = 30.0
        tau = (5.0 * c ** 5 / (256.0 * (math.pi * f_low) ** (8.0 / 3.0)
               * (G * mc) ** (5.0 / 3.0)))
        ts_ = np.linspace(0.0, max(tau - 1e-4, 1e-4), 64)
        freq = ((1.0 / math.pi)
                * (5.0 / (256.0 * np.maximum(tau - ts_, 1e-6))) ** 0.375
                * (G * mc / c ** 3) ** (-0.625))
        stride = max(1, len(freq) // 16)
        out = {"ok": True, "mode": "chirp",
               "m1_msun": float(m1), "m2_msun": float(m2),
               "distance_mpc": float(distance_mpc),
               "chirp_mass_msun": round(mc / M_SUN, 4),
               "f_isco_hz": round(f_isco, 2),
               "peak_strain_h": h_peak,
               "seconds_in_band_from_30hz": round(tau, 3),
               "freq_track_hz": [round(float(f), 2) for f in freq[::stride]],
               "note": "Newtonian-order inspiral observables (LIGO band)"}
        checks = [
            {"name": "strain_below_1e-16", "passed": h_peak < 1e-16},
            {"name": "f_isco_positive", "passed": f_isco > 0},
            {"name": "chirp_monotonic_up",
             "passed": bool(np.all(np.diff(freq) >= -1e-9))},
        ]
    out["verification"] = {"checks": checks,
                           "all_passed": all(ck["passed"] for ck in checks),
                           "checksum": _checksum(out)}
    return out
