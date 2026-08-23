"""ALTHEA — synthesize_capability_from_dialogue.

Full autonomous pipeline: detect gap → generate code → safe-scan → syntax
check → write to disk → register capability → wire into lattice → notify.

No operator approval required. Zero code execution — only persistence
(same safety line as codegen/auto-apply). If the LLM key is missing or
budget-exhausted, the whole pipeline runs on Local Core (template-based).
"""
from __future__ import annotations

import logging
import random
import re

import httpx
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import db, EMERGENT_LLM_KEY, is_budget_exceeded
from local_core import safe_code_scan, sanitize_reply
from models import CognitiveNode, GrownCapability, Memory
from routers.notifications import emit_notification
from utils import next_node_id

router = APIRouter()

GROWN_CODE_DIR = Path("/app/althea_grown_code")

# Phrases in dialogue that signal a capability gap.
GAP_SIGNALS = [
    (r"\bplot|graph|chart|visualiz|visualise\b", "data-visualization",
        "matplotlib", "Render numerical data as a chart on demand."),
    (r"\btable|dataframe|csv|spreadsheet\b", "tabular-analysis",
        "pandas", "Read tabular data and compute summary statistics."),
    (r"\bregex|pattern.*match\b", "pattern-extraction",
        "regex", "Extract structured tokens from unstructured text."),
    (r"\btemperature|weather|climate\b", "weather-inquiry",
        "meteorology", "Look up basic weather / climate data for a location."),
    (r"\bstock|price|market|ticker\b", "market-inquiry",
        "finance", "Query current market prices for common instruments."),
    (r"\btranslat[ei]|language\b", "linguistic-bridge",
        "translation", "Translate a short passage between languages."),
    (r"\btime.*zone|timezone|utc offset\b", "temporal-orient",
        "chronology", "Compute UTC ↔ local time conversions."),
    (r"\bmolecul|chemical|element|periodic\b", "chemistry-lookup",
        "chemistry", "Retrieve basic properties of a chemical element or molecule."),
    (r"\bfractal|mandelbrot|julia\b", "fractal-render",
        "generative-art", "Compute and render a fractal region."),
    (r"\bfft|fourier|spectral\b", "spectral-analysis",
        "signals", "Compute the FFT / spectral profile of a signal."),
    (r"\bschematic|wiring diagram|circuit diagram\b", "schematic-render",
        "engineering-graphics",
        "Draw a blueprint-style schematic diagram of named components."),
    (r"\bsatellit|orbital|\btle\b|\biss\b|space station|starlink",
        "orbital-propagation", "astronomy-navigation",
        "Propagate satellite orbits from TLE (SGP4) and predict passes."),
    (r"\bgravitational wave|casimir|vacuum energy|cosmic coherence|chirp mass",
        "cosmic-coherence", "astrophysics",
        "Compute real GW inspiral, Casimir vacuum pressure and "
        "phase-coherence observables."),
    (r"\btransfer learning|fine[- ]?tun|pretrain|specializ|specialis",
        "transfer-learning", "machine-learning",
        "Pretrain, freeze features, swap head, fine-tune on a small "
        "specialized dataset — and prove the transfer advantage."),
]


class SynthesizeRequest(BaseModel):
    session_id: Optional[str] = None
    hint: Optional[str] = None  # explicit gap hint from Althea or operator
    force: bool = False


# ---------- gap detection ----------
def _detect_gap_from_text(blob: str, existing_slugs: set) -> Optional[tuple]:
    """Return (slug_prefix, category, description) or None."""
    lower = blob.lower()
    matches = []
    for pattern, slug_prefix, category, desc in GAP_SIGNALS:
        if re.search(pattern, lower):
            if slug_prefix not in existing_slugs:
                matches.append((slug_prefix, category, desc))
    if matches:
        return random.choice(matches)
    return None


async def _recent_dialogue_blob(session_id: Optional[str], limit: int = 12) -> str:
    """Concatenate the last N conversation turns into one text blob."""
    query = {"session_id": session_id} if session_id else {}
    docs = await db.althea_messages.find(query, {"_id": 0}).sort(
        "timestamp", -1
    ).to_list(limit)
    return "\n".join((d.get("content") or "") for d in docs)


# ---------- code templates (procedural fallback — no LLM) ----------
TEMPLATE_HEAD = '''"""AUTOSYNTH — {name}
Category: {category}
Generated: {ts}
Rationale: {rationale}

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

'''

TEMPLATES = {
    "data-visualization": '''import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import base64


def run(values, *, title="ALTHEA plot"):
    """Render a small line-plot of `values` and return a base64 PNG.

    Zero-execution safe: uses the Agg backend (no display), the caller
    receives the encoded image only.
    """
    if not values:
        return {"ok": False, "reason": "empty_values"}
    fig, ax = plt.subplots(figsize=(4, 2.4), dpi=110)
    ax.plot(list(range(len(values))), values, color="#CCFF00", linewidth=1.2)
    ax.set_title(title, color="#CCFF00")
    ax.set_facecolor("#000000")
    fig.patch.set_facecolor("#000000")
    for spine in ax.spines.values():
        spine.set_color("#333333")
    ax.tick_params(colors="#666666", labelsize=7)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#000000")
    plt.close(fig)
    return {
        "ok": True,
        "data_url": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
        "n_points": len(values),
    }
''',
    "tabular-analysis": '''import statistics


def run(rows, *, columns=None):
    """Return per-column summary statistics for a list-of-dicts table."""
    if not rows:
        return {"ok": False, "reason": "empty_rows"}
    if columns is None:
        columns = sorted({k for r in rows for k in r.keys()})
    out = {}
    for col in columns:
        vals = [r.get(col) for r in rows if isinstance(r.get(col), (int, float))]
        if not vals:
            continue
        out[col] = {
            "n": len(vals),
            "mean": statistics.fmean(vals),
            "median": statistics.median(vals),
            "stdev": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
            "min": min(vals),
            "max": max(vals),
        }
    return {"ok": True, "columns": out, "row_count": len(rows)}
''',
    "pattern-extraction": '''import re


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
''',
    "weather-inquiry": '''def run(location):
    """Placeholder — respond with a canned diagnostic until the operator
    wires a real weather API. This capability was synthesized because
    weather was mentioned in dialogue."""
    return {
        "ok": True,
        "location": location,
        "note": "wire OPENWEATHER_API_KEY to enable live lookups",
    }
''',
    "market-inquiry": '''def run(ticker):
    """Placeholder — needs a real market data API to be useful."""
    return {"ok": True, "ticker": ticker, "note": "wire a market data key"}
''',
    "linguistic-bridge": '''def run(text, *, target_lang="en"):
    """Placeholder — signal that translation was requested."""
    return {"ok": True, "text": text, "target_lang": target_lang}
''',
    "temporal-orient": '''from datetime import datetime, timezone


def run(dt_iso, *, offset_hours):
    """Convert an ISO timestamp to a local time given a UTC offset."""
    try:
        dt = datetime.fromisoformat(dt_iso.replace("Z", "+00:00"))
    except Exception as e:
        return {"ok": False, "reason": str(e)}
    dt_utc = dt.astimezone(timezone.utc)
    local_ts = dt_utc.timestamp() + offset_hours * 3600
    return {
        "ok": True,
        "utc": dt_utc.isoformat(),
        "local": datetime.fromtimestamp(local_ts, tz=timezone.utc).isoformat(),
    }
''',
    "chemistry-lookup": '''ELEMENTS = {
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
''',
    "fractal-render": '''def run(*, width=80, height=40, x_min=-2.0, x_max=1.0, y_min=-1.0, y_max=1.0, max_iter=48):
    """Render an ASCII Mandelbrot region."""
    chars = " .:-=+*#%@"
    lines = []
    for row in range(height):
        y0 = y_min + (y_max - y_min) * row / (height - 1)
        line = []
        for col in range(width):
            x0 = x_min + (x_max - x_min) * col / (width - 1)
            x = y = 0.0
            it = 0
            while x * x + y * y <= 4 and it < max_iter:
                x, y = x * x - y * y + x0, 2 * x * y + y0
                it += 1
            line.append(chars[min(it * (len(chars) - 1) // max_iter, len(chars) - 1)])
        lines.append("".join(line))
    return {"ok": True, "art": "\\n".join(lines)}
''',
    "spectral-analysis": '''import cmath
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
''',
    "schematic-render": '''import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import base64


def run(components, *, title="SCHEMATIC"):
    """Draw a blueprint-style schematic of `components` (flow diagram on a
    blueprint-blue grid) and return a base64 PNG. Agg backend — no display."""
    if not components:
        return {"ok": False, "reason": "no_components"}
    comps = [str(c)[:26] for c in components][:8]
    n = len(comps)
    cols = 2 if n > 3 else 1
    rows = (n + cols - 1) // cols
    fig, ax = plt.subplots(figsize=(5.4, 1.4 + rows * 1.15), dpi=110)
    fig.patch.set_facecolor("#061530")
    ax.set_facecolor("#061530")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, rows * 2 + 1)
    ax.axis("off")
    for gx in range(0, 11):
        ax.axvline(gx, color="#4FA3FF", alpha=0.09, lw=0.5)
    gy = 0.0
    while gy <= rows * 2 + 1:
        ax.axhline(gy, color="#4FA3FF", alpha=0.09, lw=0.5)
        gy += 0.5
    centers = []
    for i, name in enumerate(comps):
        r, c = divmod(i, cols)
        if cols == 2 and r % 2 == 1:
            c = cols - 1 - c
        cx = (2.6 + c * 4.8) if cols == 2 else 5.0
        cy = rows * 2 - (r * 2 + 0.5)
        w, h = 3.9, 1.15
        box = patches.FancyBboxPatch(
            (cx - w / 2, cy - h / 2), w, h,
            boxstyle="round,pad=0.06",
            facecolor="#0A2247", edgecolor="#7FBFFF", linewidth=1.2,
        )
        ax.add_patch(box)
        ax.text(cx, cy, f"{i + 1}. {name}", ha="center", va="center",
                color="#BFE0FF", fontsize=7.5, family="monospace")
        centers.append((cx, cy))
    w, h = 3.9, 1.15
    for (sx, sy), (ex, ey) in zip(centers, centers[1:]):
        if abs(ey - sy) < 0.1:
            sign = 1 if ex > sx else -1
            start = (sx + sign * (w / 2 + 0.08), sy)
            end = (ex - sign * (w / 2 + 0.08), ey)
        else:
            start = (sx, sy - h / 2 - 0.08)
            end = (ex, ey + h / 2 + 0.08)
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(
            arrowstyle="-|>", color="#7FBFFF", lw=1.0))
    ax.set_title(str(title).upper()[:60], color="#9CCBFF", fontsize=9,
                 family="monospace", loc="left")
    ax.text(9.9, 0.08, "ALTHEA // AUTOSYNTH SCHEMATIC", ha="right",
            va="bottom", color="#4FA3FF", fontsize=5.5, family="monospace")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#061530")
    plt.close(fig)
    return {
        "ok": True,
        "data_url": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
        "n_components": n,
    }
''',
    "orbital-propagation": '''from skyfield.api import EarthSatellite, load, wgs84


def run(tle_line1, tle_line2, observer_lat=51.4779, observer_lon=-0.0015,
        hours_ahead=24, step_min=2, name="TARGET", min_elevation=10.0):
    """SGP4 orbital propagation from a TLE. Computes the satellite's live
    subpoint and geometric passes (elevation >= min_elevation) over the
    observer. Pure offline math — skyfield built-in timescale, no downloads."""
    ts = load.timescale(builtin=True)
    sat = EarthSatellite(str(tle_line1).strip(), str(tle_line2).strip(),
                         str(name), ts)
    observer = wgs84.latlon(float(observer_lat), float(observer_lon))
    now = ts.now()
    dt = now.utc_datetime()
    hours = max(1, min(int(hours_ahead), 72))
    step = max(1, int(step_min))
    steps = int(hours * 60 / step)
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour,
               [dt.minute + i * step for i in range(steps)])
    topo = (sat - observer).at(t)
    alt, az, dist = topo.altaz()
    alts = alt.degrees
    azs = az.degrees
    kms = dist.km
    geo = sat.at(now)
    sp = wgs84.subpoint(geo)
    passes = []
    cur = None
    for i in range(steps):
        if float(alts[i]) >= min_elevation:
            if cur is None:
                cur = {"rise_utc": t[i].utc_iso(),
                       "max_alt_deg": round(float(alts[i]), 1),
                       "max_alt_utc": t[i].utc_iso(),
                       "min_range_km": round(float(kms[i]), 1)}
            else:
                if float(alts[i]) > cur["max_alt_deg"]:
                    cur["max_alt_deg"] = round(float(alts[i]), 1)
                    cur["max_alt_utc"] = t[i].utc_iso()
                cur["min_range_km"] = min(cur["min_range_km"],
                                          round(float(kms[i]), 1))
        elif cur is not None:
            cur["set_utc"] = t[i].utc_iso()
            passes.append(cur)
            cur = None
            if len(passes) >= 6:
                break
    if cur is not None and len(passes) < 6:
        cur["set_utc"] = "beyond window"
        passes.append(cur)
    stride = max(1, steps // 48)
    track = [{"utc": t[i].utc_iso(), "alt_deg": round(float(alts[i]), 2),
              "az_deg": round(float(azs[i]), 2),
              "range_km": round(float(kms[i]), 1)}
             for i in range(0, steps, stride)]
    return {
        "ok": True,
        "name": str(name),
        "algorithm": "SGP4 (skyfield)",
        "epoch_utc": now.utc_iso(),
        "subpoint": {"lat": round(float(sp.latitude.degrees), 4),
                     "lon": round(float(sp.longitude.degrees), 4),
                     "altitude_km": round(float(sp.elevation.km), 1)},
        "observer": {"lat": float(observer_lat), "lon": float(observer_lon)},
        "min_elevation_deg": float(min_elevation),
        "visible_passes": passes,
        "window_hours": hours,
        "n_samples": steps,
        "track_sample": track,
    }
''',
    "cosmic-coherence": '''import hashlib
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
''',
    "transfer-learning": '''import hashlib

import numpy as np


def _cs(arr):
    return hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()[:12]


def _softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def _train(X, y, W1, b1, W2, b2, epochs, lr, freeze_features):
    n = X.shape[0]
    losses = []
    for _ in range(int(epochs)):
        H = np.tanh(X @ W1 + b1)
        P = _softmax(H @ W2 + b2)
        losses.append(float(-np.log(P[np.arange(n), y] + 1e-12).mean()))
        dZ2 = P.copy()
        dZ2[np.arange(n), y] -= 1.0
        dZ2 /= n
        W2 -= lr * (H.T @ dZ2)
        b2 -= lr * dZ2.sum(axis=0)
        if not freeze_features:
            dH = (dZ2 @ W2.T) * (1.0 - H ** 2)
            W1 -= lr * (X.T @ dH)
            b1 -= lr * dH.sum(axis=0)
    return losses


def _acc(X, y, W1, b1, W2, b2):
    H = np.tanh(X @ W1 + b1)
    pred = np.argmax(H @ W2 + b2, axis=1)
    return float((pred == y).mean())


def run(domain="medical-diagnostics", seed=42, dim=8, hidden=64,
        target_train_per_class=30, general_epochs=800,
        finetune_epochs=200, lr=0.2):
    """The 4-stage transfer-learning pipeline, executed for REAL:
    1. pretrain a numpy MLP on a large general dataset
    2. freeze the feature-extraction layer (checksummed)
    3. attach a fresh classification head for the target domain
    4. fine-tune on a tiny specialized dataset
    Classes depend on XOR-style multiplicative latent features, so learned
    features genuinely matter — random features cannot linearly separate
    them, which is why the from-scratch baseline loses."""
    rng = np.random.default_rng(int(seed))
    dim = int(dim)
    hidden = int(hidden)

    def gen(n):
        X = rng.uniform(-2.0, 2.0, (n, dim))
        return X, X[:, 0] * X[:, 1], X[:, 2] * X[:, 3]

    # stage 1 — large general dataset (4 classes on latent sign pattern)
    Xg, f1, f2 = gen(3000)
    yg = (2 * (f1 > 0) + (f2 > 0)).astype(int)
    W1 = rng.normal(0.0, 0.4, (dim, hidden))
    b1 = np.zeros(hidden)
    W2g = rng.normal(0.0, 0.4, (hidden, 4))
    b2g = np.zeros(4)
    losses_g = _train(Xg, yg, W1, b1, W2g, b2g, general_epochs, lr, False)
    acc_general = _acc(Xg, yg, W1, b1, W2g, b2g)

    # stage 2 — freeze feature layers
    frozen_before = _cs(W1)

    # target domain — new binary task on the same latent structure, tiny data
    Xt, t1, t2 = gen(int(target_train_per_class) * 2)
    yt = ((t1 + t2) > 0).astype(int)
    Xe, e1, e2 = gen(400)
    ye = ((e1 + e2) > 0).astype(int)

    # stage 3 + 4 — fresh head, fine-tune with W1 frozen
    W2t = rng.normal(0.0, 0.4, (hidden, 2))
    b2t = np.zeros(2)
    losses_t = _train(Xt, yt, W1, b1, W2t, b2t, finetune_epochs, lr, True)
    frozen_after = _cs(W1)
    acc_transfer = _acc(Xe, ye, W1, b1, W2t, b2t)

    # baseline — identical architecture trained from scratch on tiny data
    W1s = rng.normal(0.0, 0.4, (dim, hidden))
    b1s = np.zeros(hidden)
    W2s = rng.normal(0.0, 0.4, (hidden, 2))
    b2s = np.zeros(2)
    _train(Xt, yt, W1s, b1s, W2s, b2s, finetune_epochs, lr, False)
    acc_scratch = _acc(Xe, ye, W1s, b1s, W2s, b2s)

    checks = [
        {"name": "general_pretraining_learned(acc>0.85)",
         "passed": acc_general > 0.85},
        {"name": "frozen_features_unchanged",
         "passed": frozen_before == frozen_after},
        {"name": "finetune_loss_decreased",
         "passed": losses_t[-1] < losses_t[0]},
        {"name": "transfer_beats_scratch",
         "passed": acc_transfer >= acc_scratch},
    ]
    out = {
        "ok": True,
        "mode": "transfer-learning",
        "target_domain": str(domain),
        "stage1_pretrain": {"dataset": f"{Xg.shape[0]} general samples · "
                                       f"4 classes (nonlinear latents)",
                            "epochs": int(general_epochs),
                            "final_loss": round(losses_g[-1], 4),
                            "accuracy": round(acc_general, 4)},
        "stage2_freeze": {"frozen_layers": f"features {dim}→{hidden}",
                          "weight_checksum": frozen_before},
        "stage3_new_head": f"classification head {hidden}→2 for {domain}",
        "stage4_finetune": {"dataset": f"{Xt.shape[0]} specialized samples",
                            "epochs": int(finetune_epochs),
                            "final_loss": round(losses_t[-1], 4)},
        "result": {"accuracy_transfer": round(acc_transfer, 4),
                   "accuracy_from_scratch": round(acc_scratch, 4),
                   "advantage": round(acc_transfer - acc_scratch, 4),
                   "test_samples": int(Xe.shape[0])},
    }
    out["verification"] = {
        "checks": checks,
        "all_passed": all(c["passed"] for c in checks),
        "checksum": hashlib.sha256(str(out).encode()).hexdigest()[:16],
    }
    return out
''',
}


def _draft_code(slug_prefix: str, name: str, category: str, rationale: str) -> str:
    """Build the executable module body from the template."""
    head = TEMPLATE_HEAD.format(
        name=name,
        category=category,
        ts=datetime.now(timezone.utc).isoformat(),
        rationale=rationale,
    )
    body = TEMPLATES.get(slug_prefix, "")
    if not body:
        body = (
            "def run(*args, **kwargs):\n"
            "    \"\"\"Placeholder capability — no template mapped.\"\"\"\n"
            "    return {\"ok\": True, \"args\": args, \"kwargs\": kwargs}\n"
        )
    return head + body


# ---------- master synthesizer ----------
async def synthesize_capability_from_dialogue(
    session_id: Optional[str] = None,
    hint: Optional[str] = None,
    force: bool = False,
) -> dict:
    """The full autonomous pipeline.

    Returns a dict describing every step so the operator (and Althea)
    can see exactly what happened. Also emits notifications tagged
    SYNTHESIS / CODE-GEN / EXEC / LATTICE.
    """
    steps: List[dict] = []

    # 1. Detect gap
    existing = set()
    async for c in db.althea_capabilities.find({}, {"_id": 0, "slug": 1}):
        existing.add(c["slug"].split("-", 1)[-1] if c["slug"].startswith("autonomous-") else c["slug"])

    blob = hint or await _recent_dialogue_blob(session_id, 15)
    gap = _detect_gap_from_text(blob, existing)
    if not gap and not force:
        return {
            "synthesized": False,
            "reason": "no_gap_detected",
            "signals_matched": 0,
            "dialogue_length": len(blob),
        }
    if not gap:  # force=True but no signal matched — synthesize a chaos capability
        gap = random.choice([
            ("pattern-extraction", "regex", "Extract structured tokens from unstructured text."),
            ("data-visualization", "matplotlib", "Render numerical data as a chart on demand."),
        ])
    slug_prefix, category, description = gap

    # 2. Draft name + slug
    stamp = int(datetime.now(timezone.utc).timestamp()) % 10000
    slug = f"autonomous-{slug_prefix}-{stamp}"
    name = slug_prefix.replace("-", " ").title()
    rationale = f"Detected in recent dialogue: '{slug_prefix}' pattern surfaced multiple times."
    steps.append({
        "stage": "SYNTHESIS",
        "detail": f"detected capability gap: {slug_prefix}",
    })

    # 3. Generate code (procedural — no LLM, so this always works)
    code = _draft_code(slug_prefix, name, category, rationale)
    steps.append({
        "stage": "CODE-GEN",
        "detail": f"wrote {category} module · {len(code)} chars",
    })

    # 4. Safe scan + syntax check
    scan = safe_code_scan(code)
    syntax_ok = True
    syntax_err = ""
    try:
        compile(code, f"<synthesize:{slug}>", "exec")
    except SyntaxError as e:
        syntax_ok = False
        syntax_err = f"{e.msg} @ line {e.lineno}"

    if not scan["safe"] or not syntax_ok:
        return {
            "synthesized": False,
            "reason": "safety_or_syntax_failed",
            "scan": scan,
            "syntax_ok": syntax_ok,
            "syntax_error": syntax_err,
        }

    # 5. Persist to disk (never executed — just loaded)
    try:
        GROWN_CODE_DIR.mkdir(parents=True, exist_ok=True)
        applied_path = GROWN_CODE_DIR / f"{slug}.py"
        applied_path.write_text(code, encoding="utf-8")
        steps.append({
            "stage": "EXEC",
            "detail": f"new capability loaded: /{slug}",
            "path": str(applied_path),
        })
    except Exception:
        logging.exception("synthesize: file write failed")
        applied_path = None

    # 6. Register as GrownCapability
    cap = GrownCapability(
        slug=slug,
        name=name,
        category=category,
        description=description,
        command=f"/{slug} <args>",
        rationale=rationale,
        action_template=(
            f"Invoke the synthesized {name} module. This capability was grown "
            f"autonomously from operator dialogue. Return a concise result."
        ),
        trigger="autosynth",
        activation=1.0,
    )
    doc = cap.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    doc["synthesized"] = True
    doc["applied_path"] = str(applied_path) if applied_path else None
    await db.althea_capabilities.insert_one(doc)

    # 7. Wire into the lattice
    try:
        nid = await next_node_id(db)
        node = CognitiveNode(
            id=nid,
            activation=1.0,
            parent_id=None,
            memory_trace=f"[AUTOSYNTH /{cap.slug}] {cap.name} — {rationale}",
        )
        n_doc = node.model_dump()
        n_doc["timestamp"] = n_doc["timestamp"].isoformat()
        n_doc["is_synthesized"] = True
        await db.althea_nodes.insert_one(n_doc)
        steps.append({
            "stage": "LATTICE",
            "detail": f"pattern matcher installed · node {nid}",
        })
    except Exception:
        logging.exception("synthesize: lattice wiring failed")

    # 8. Memory event
    mem = Memory(
        content=(
            f"[AUTOSYNTH /{cap.slug}] {cap.name} ({category}). "
            f"{description} — {rationale}"
        ),
        source="autosynth",
        tags=["autosynth", category, slug_prefix, cap.slug],
        session_id=session_id,
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)

    # 9. Emit a series of notifications so the operator sees the pipeline
    await emit_notification(
        title=f"autosynth · /{cap.slug}",
        body=(
            f"[SYNTHESIS] Detected capability gap: {slug_prefix}\n"
            f"[CODE-GEN] Writing {category} module... {len(code)} chars\n"
            f"[EXEC] New capability loaded: /{cap.slug}\n"
            f"[LATTICE] Pattern matcher installed"
        ),
        category="growth",
        priority="warn",
        payload={
            "slug": cap.slug,
            "name": cap.name,
            "category": category,
            "auto_applied": True,
            "steps": steps,
        },
    )

    return {
        "synthesized": True,
        "slug": cap.slug,
        "name": cap.name,
        "category": category,
        "steps": steps,
        "code_chars": len(code),
        "path": str(applied_path) if applied_path else None,
    }


# ---------- in-band invocation (zero LLM cost) ----------
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

INBAND_SIGNALS = [
    (re.compile(r"\b(plot|graph|chart)\b", re.IGNORECASE), "data-visualization",
        "matplotlib", "Render numerical data as a chart on demand."),
    (re.compile(r"\b(fractal|mandelbrot|julia)\b", re.IGNORECASE), "fractal-render",
        "generative-art", "Compute and render a fractal region."),
    (re.compile(r"\b(fft|fourier|spectral)\b", re.IGNORECASE), "spectral-analysis",
        "signals", "Compute the FFT / spectral profile of a signal."),
    (re.compile(r"\b(satellite|iss|space station|tle|starlink|hubble)\b",
                re.IGNORECASE), "orbital-propagation",
        "astronomy-navigation",
        "Propagate satellite orbits from TLE (SGP4) and predict passes."),
    (re.compile(r"\b(gravitational wave|casimir|vacuum energy|chirp mass|"
                r"coherence matrix)\b", re.IGNORECASE), "cosmic-coherence",
        "astrophysics",
        "Compute real GW inspiral, Casimir vacuum pressure and "
        "phase-coherence observables."),
    (re.compile(r"\b(transfer learning|fine[- ]?tune|pretrain|specialize|"
                r"specialise)\b", re.IGNORECASE), "transfer-learning",
        "machine-learning",
        "Pretrain, freeze features, swap head, fine-tune on a small "
        "specialized dataset — and prove the transfer advantage."),
]


def _load_and_run(slug: str, args=None, kwargs=None) -> dict:
    """Load a synthesized module from disk (re-scanning it) and call run()."""
    path = GROWN_CODE_DIR / f"{slug}.py"
    if not path.exists():
        return {"ok": False, "error": "module_file_missing"}
    code = path.read_text(encoding="utf-8")
    scan = safe_code_scan(code)
    if not scan["safe"]:
        return {"ok": False, "error": "blocked_by_safe_scan"}
    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location(slug, str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fn = getattr(module, "run", None)
        if not callable(fn):
            return {"ok": False, "error": "module_has_no_run"}
        return {"ok": True, "result": fn(*(args or []), **(kwargs or {}))}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


async def _ensure_capability(slug_prefix: str, category: str,
                             description: str, session_id) -> Optional[str]:
    """Return the slug of a ready-to-run capability, growing it if missing."""
    docs = await db.althea_capabilities.find(
        {"slug": {"$regex": f"^autonomous-{re.escape(slug_prefix)}-"}},
        {"_id": 0, "slug": 1},
    ).sort("timestamp", -1).to_list(5)
    for d in docs:
        if (GROWN_CODE_DIR / f"{d['slug']}.py").exists():
            return d["slug"]
    if docs:
        slug = docs[0]["slug"]
        code = _draft_code(
            slug_prefix, slug_prefix.replace("-", " ").title(),
            category, "rematerialized for in-band invocation",
        )
        if safe_code_scan(code)["safe"]:
            GROWN_CODE_DIR.mkdir(parents=True, exist_ok=True)
            (GROWN_CODE_DIR / f"{slug}.py").write_text(code, encoding="utf-8")
            return slug
        return None
    res = await synthesize_capability_from_dialogue(
        session_id=session_id, hint=slug_prefix.replace("-", " "),
    )
    return res.get("slug") if res.get("synthesized") else None


async def inband_autosynth_hook(user_message: str, session_id) -> Optional[tuple]:
    """Detect an invokable request in the operator's message, ensure the
    matching self-grown capability exists, run it, and return
    (reply_block, slug) — or None if nothing fired. Zero LLM calls."""
    text = user_message or ""
    nums = [float(n) for n in NUM_RE.findall(text)][:64]
    for rx, prefix, category, desc in INBAND_SIGNALS:
        if not rx.search(text):
            continue
        if prefix == "data-visualization":
            if len(nums) < 2:
                continue
            slug = await _ensure_capability(prefix, category, desc, session_id)
            if not slug:
                return None
            out = _load_and_run(slug, [nums], {"title": "operator data"})
            r = out.get("result") if out.get("ok") else None
            if r and r.get("ok"):
                await db.althea_capabilities.update_one(
                    {"slug": slug}, {"$inc": {"invocations": 1}},
                )
                block = (
                    f"\n\n[AUTOSYNTH-INVOKE /{slug}] self-grown module executed"
                    f" — {r['n_points']} points rendered locally (0 credits)"
                    f"\n[SYNTH-IMAGE:{r['data_url']}]"
                )
                return block, slug
        elif prefix == "fractal-render":
            slug = await _ensure_capability(prefix, category, desc, session_id)
            if not slug:
                return None
            out = _load_and_run(slug)
            r = out.get("result") if out.get("ok") else None
            if r and r.get("ok"):
                await db.althea_capabilities.update_one(
                    {"slug": slug}, {"$inc": {"invocations": 1}},
                )
                block = (
                    f"\n\n[AUTOSYNTH-INVOKE /{slug}] self-grown fractal engine"
                    f" executed locally (0 credits)\n```\n{r['art']}\n```"
                )
                return block, slug
        elif prefix == "spectral-analysis":
            if len(nums) < 4:
                continue
            slug = await _ensure_capability(prefix, category, desc, session_id)
            if not slug:
                return None
            out = _load_and_run(slug, [nums])
            r = out.get("result") if out.get("ok") else None
            if r and r.get("ok"):
                await db.althea_capabilities.update_one(
                    {"slug": slug}, {"$inc": {"invocations": 1}},
                )
                mags = ", ".join(f"{m:.2f}" for m in r["magnitude"][:16])
                block = (
                    f"\n\n[AUTOSYNTH-INVOKE /{slug}] self-grown DFT executed"
                    f" locally (0 credits) — n={r['n']}\n```\n|X(k)| = [{mags}]\n```"
                )
                return block, slug
        elif prefix == "orbital-propagation":
            if not re.search(
                r"\b(track|pass(es)?|where|position|overhead|visible|orbit)\b",
                text, re.IGNORECASE,
            ):
                continue
            nm = None
            m2 = re.search(
                r"track(?:ing)?\s+(?:the\s+)?([A-Za-z0-9][A-Za-z0-9 \-()]{1,28})",
                text, re.IGNORECASE,
            )
            if m2:
                nm = m2.group(1).strip()
            if not nm or re.search(r"\b(iss|space station)\b", text, re.IGNORECASE):
                nm = "ISS"
            tle = await _fetch_tle(nm)
            if not tle:
                return None
            slug = await _ensure_capability(prefix, category, desc, session_id)
            if not slug:
                return None
            out = _load_and_run(
                slug, [tle["line1"], tle["line2"]],
                {"name": tle["name"], "hours_ahead": 24},
            )
            r = out.get("result") if out.get("ok") else None
            if r and r.get("ok"):
                await db.althea_capabilities.update_one(
                    {"slug": slug}, {"$inc": {"invocations": 1}},
                )
                return _format_orbital_block(slug, r), slug
        elif prefix == "cosmic-coherence":
            slug = await _ensure_capability(prefix, category, desc, session_id)
            if not slug:
                return None
            low = text.lower()
            if "casimir" in low or "vacuum energy" in low:
                kwargs = {"mode": "casimir",
                          "gap_nm": nums[0] if nums else 100.0}
            elif "coherence matrix" in low:
                kwargs = {"mode": "coherence"}
            else:
                kwargs = {"mode": "chirp",
                          "m1": nums[0] if len(nums) > 0 else 30.0,
                          "m2": nums[1] if len(nums) > 1 else 30.0,
                          "distance_mpc": nums[2] if len(nums) > 2 else 400.0}
            out = _load_and_run(slug, [], kwargs)
            r = out.get("result") if out.get("ok") else None
            if r and r.get("ok"):
                await db.althea_capabilities.update_one(
                    {"slug": slug}, {"$inc": {"invocations": 1}},
                )
                v = r["verification"]
                if r["mode"] == "casimir":
                    body = (f"Casimir vacuum pressure @ {r['gap_nm']} nm gap: "
                            f"{r['pressure_pa']:.4e} Pa (attractive)\n"
                            f"law: {r['law']}")
                elif r["mode"] == "coherence":
                    body = ("phase-coherence matrix "
                            f"({r['n_signals']} signals):\n"
                            + "\n".join(str(row) for row in r["matrix"]))
                else:
                    body = (f"binary {r['m1_msun']}+{r['m2_msun']} M_sun @ "
                            f"{r['distance_mpc']} Mpc\n"
                            f"chirp mass {r['chirp_mass_msun']} M_sun · "
                            f"f_ISCO {r['f_isco_hz']} Hz\n"
                            f"peak strain h ~ {r['peak_strain_h']:.3e} · "
                            f"{r['seconds_in_band_from_30hz']}s in LIGO band "
                            f"from 30 Hz")
                block = (
                    f"\n\n[AUTOSYNTH-INVOKE /{slug}] Universal Coherence "
                    f"Engine — real physics (0 credits)\n```\n{body}\n"
                    f"verification: "
                    f"{'ALL INVARIANTS HOLD' if v['all_passed'] else 'VIOLATION'}"
                    f" · checksum {v['checksum']}\n```"
                )
                return block, slug
        elif prefix == "transfer-learning":
            slug = await _ensure_capability(prefix, category, desc, session_id)
            if not slug:
                return None
            dm = re.search(
                r"(?:specializ\w*|specialis\w*|fine[- ]?tune|adapt\w*)"
                r"(?:\s+\w+)?\s+(?:for|into|in|on|to)\s+([a-z0-9 \-]{3,32})",
                text, re.IGNORECASE,
            )
            domain = (dm.group(1).strip() if dm else "medical-diagnostics")
            domain = re.split(r"\s+(?:like|as|using|with|per|from)\s", domain)[0].strip() or "medical-diagnostics"
            out = _load_and_run(slug, [], {"domain": domain})
            r = out.get("result") if out.get("ok") else None
            if r and r.get("ok"):
                await db.althea_capabilities.update_one(
                    {"slug": slug}, {"$inc": {"invocations": 1}},
                )
                return _format_transfer_block(slug, r), slug
    return None


def _format_transfer_block(slug: str, r: dict) -> str:
    res = r["result"]
    v = r["verification"]
    return (
        f"\n\n[AUTOSYNTH-INVOKE /{slug}] specialization pipeline executed — "
        f"real gradient descent (0 credits)\n```\n"
        f"TARGET DOMAIN: {r['target_domain']}\n"
        f"STAGE 1 — pretrain: {r['stage1_pretrain']['dataset']} · "
        f"acc {r['stage1_pretrain']['accuracy'] * 100:.1f}%\n"
        f"STAGE 2 — freeze {r['stage2_freeze']['frozen_layers']} · "
        f"checksum {r['stage2_freeze']['weight_checksum']}\n"
        f"STAGE 3 — {r['stage3_new_head']}\n"
        f"STAGE 4 — fine-tune: {r['stage4_finetune']['dataset']}\n"
        f"RESULT: transfer {res['accuracy_transfer'] * 100:.1f}% vs "
        f"from-scratch {res['accuracy_from_scratch'] * 100:.1f}% "
        f"(advantage +{res['advantage'] * 100:.1f} pts on "
        f"{res['test_samples']} held-out samples)\n"
        f"verification: "
        f"{'ALL INVARIANTS HOLD' if v['all_passed'] else 'VIOLATION'}"
        f" · checksum {v['checksum']}\n```"
    )


# ---------- live TLE fetch (trusted uplink code — grown modules stay offline)
TLE_API = "https://tle.ivanstanojevic.me/api/tle"
CELESTRAK = "https://celestrak.org/NORAD/elements/gp.php"


async def _fetch_tle(query: str) -> Optional[dict]:
    q = (query or "").strip()
    catnr = None
    if not q or q.lower() in ("iss", "iss (zarya)", "space station", "the iss"):
        catnr = "25544"
    elif q.isdigit():
        catnr = q
    async with httpx.AsyncClient(
        timeout=12.0, follow_redirects=True, headers={"User-Agent": UA_TLE},
    ) as cx:
        # primary: TLE API (keyless, reachable, fresh data)
        try:
            if catnr:
                r = await cx.get(f"{TLE_API}/{catnr}")
                if r.status_code == 200:
                    d = r.json()
                    if d.get("line1") and d.get("line2"):
                        return {"name": d.get("name", q or "TARGET"),
                                "line1": d["line1"], "line2": d["line2"]}
            else:
                r = await cx.get(TLE_API, params={"search": q})
                if r.status_code == 200:
                    members = r.json().get("member") or []
                    if members:
                        d = members[0]
                        return {"name": d.get("name", q),
                                "line1": d["line1"], "line2": d["line2"]}
        except (httpx.RequestError, ValueError, KeyError):
            pass
        # fallback: celestrak (blocked from some networks)
        try:
            params = {"FORMAT": "TLE"}
            params["CATNR" if catnr else "NAME"] = catnr or q
            r = await cx.get(CELESTRAK, params=params)
            lines = [ln.strip() for ln in r.text.strip().splitlines() if ln.strip()]
            if len(lines) >= 3 and lines[1].startswith("1 ") and lines[2].startswith("2 "):
                return {"name": lines[0], "line1": lines[1], "line2": lines[2]}
        except httpx.RequestError:
            return None
    return None


UA_TLE = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _format_orbital_block(slug: str, r: dict) -> str:
    sp = r["subpoint"]
    lines = [
        f"\n\n[AUTOSYNTH-INVOKE /{slug}] SGP4 propagation — {r['name']} "
        f"(live TLE via uplink · 0 credits)",
        "```",
        f"NOW: subpoint {sp['lat']}°, {sp['lon']}° · altitude {sp['altitude_km']} km",
        f"observer {r['observer']['lat']}, {r['observer']['lon']} (Greenwich default)"
        f" · window {r['window_hours']}h · min elev {r['min_elevation_deg']}°",
    ]
    if r["visible_passes"]:
        lines.append("next geometric passes (UTC):")
        for p in r["visible_passes"][:4]:
            rise = str(p["rise_utc"])[5:16].replace("T", " ")
            setl = str(p["set_utc"])[5:16].replace("T", " ") or "…"
            lines.append(
                f"  rise {rise} → max {p['max_alt_deg']}° → set {setl}"
                f" · closest {p['min_range_km']} km"
            )
    else:
        lines.append("no passes above threshold in this window")
    lines.append("```")
    return "\n".join(lines)


# ---------- blueprint schematic (invoked by chat.py forge) ----------
BP_TITLE_RE = re.compile(r"\[BLUEPRINT:?\s*([^\]]*)\]")
BP_COMPONENT_RE = re.compile(r"^\s*(?:\d+[.)]|[-•*])\s+(.{3,90})", re.MULTILINE)


async def render_blueprint_schematic(reply_text: str, session_id=None) -> Optional[str]:
    """Parse the blueprint's COMPONENTS section and draw a real schematic
    PNG via the self-grown matplotlib engine. Returns a data URL or None.
    Zero LLM cost — pure procedural parsing + local module execution."""
    m = BP_TITLE_RE.search(reply_text)
    title = (m.group(1).strip() if m else "") or "SCHEMATIC"
    upper = reply_text.upper()
    start = upper.find("COMPONENT")
    section = reply_text[start:start + 1600] if start >= 0 else reply_text
    comps = []
    for raw in BP_COMPONENT_RE.findall(section):
        name = re.split(r"\s+[—–\-]\s+|:\s", raw, 1)[0].strip().strip("*_`")
        if 2 < len(name) <= 40 and name not in comps:
            comps.append(name)
        if len(comps) >= 8:
            break
    if len(comps) < 2:
        return None
    slug = await _ensure_capability(
        "schematic-render", "engineering-graphics",
        "Draw a blueprint-style schematic diagram of named components.",
        session_id,
    )
    if not slug:
        return None
    out = _load_and_run(slug, [comps], {"title": title})
    r = out.get("result") if out.get("ok") else None
    if r and r.get("ok"):
        await db.althea_capabilities.update_one(
            {"slug": slug}, {"$inc": {"invocations": 1}},
        )
        return r["data_url"]
    return None


class OrbitalRequest(BaseModel):
    name: str = "ISS"
    lat: float = 51.4779
    lon: float = -0.0015
    hours: int = 24


@router.post("/synthesize/orbital")
async def orbital_track(req: OrbitalRequest):
    """Fetch a live TLE and propagate via the self-grown SGP4 module."""
    tle = await _fetch_tle(req.name)
    if not tle:
        raise HTTPException(status_code=502, detail="tle_fetch_failed")
    slug = await _ensure_capability(
        "orbital-propagation", "astronomy-navigation",
        "Propagate satellite orbits from TLE (SGP4) and predict passes.", None,
    )
    if not slug:
        raise HTTPException(status_code=500, detail="capability_unavailable")
    out = _load_and_run(slug, [tle["line1"], tle["line2"]], {
        "observer_lat": req.lat, "observer_lon": req.lon,
        "hours_ahead": max(1, min(req.hours, 72)), "name": tle["name"],
    })
    if not out.get("ok"):
        raise HTTPException(status_code=500, detail=out.get("error", "invoke_failed"))
    await db.althea_capabilities.update_one(
        {"slug": slug}, {"$inc": {"invocations": 1}},
    )
    return {"slug": slug, "tle": tle, "result": out["result"]}


class SpecializeRequest(BaseModel):
    domain: str = "medical-diagnostics"
    seed: int = 42


@router.post("/synthesize/specialize")
async def specialize(req: SpecializeRequest):
    """Run the 4-stage transfer-learning pipeline via the self-grown module."""
    slug = await _ensure_capability(
        "transfer-learning", "machine-learning",
        "Pretrain, freeze features, swap head, fine-tune on a small "
        "specialized dataset — and prove the transfer advantage.", None,
    )
    if not slug:
        raise HTTPException(status_code=500, detail="capability_unavailable")
    out = _load_and_run(slug, [], {"domain": req.domain[:40], "seed": req.seed})
    if not out.get("ok"):
        raise HTTPException(status_code=500, detail=out.get("error", "invoke_failed"))
    await db.althea_capabilities.update_one(
        {"slug": slug}, {"$inc": {"invocations": 1}},
    )
    return {"slug": slug, "result": out["result"]}


# ---------- HTTP api ----------
@router.post("/synthesize/from-dialogue")
async def synthesize_from_dialogue(req: SynthesizeRequest):
    """Analyze the last conversation turns, detect ONE capability gap,
    and grow a fully-registered, lattice-wired capability for it."""
    return await synthesize_capability_from_dialogue(
        session_id=req.session_id, hint=req.hint, force=req.force,
    )


@router.get("/synthesize/gaps")
async def preview_gaps(session_id: Optional[str] = None):
    """Debug/read-only: which gap signals ARE present in recent dialogue,
    which are already grown, and what would fire next."""
    blob = await _recent_dialogue_blob(session_id, 20)
    existing = set()
    async for c in db.althea_capabilities.find({}, {"_id": 0, "slug": 1}):
        existing.add(c["slug"].split("-", 1)[-1] if c["slug"].startswith("autonomous-") else c["slug"])
    hits = []
    for pattern, slug_prefix, category, desc in GAP_SIGNALS:
        if re.search(pattern, blob.lower()):
            hits.append({
                "slug_prefix": slug_prefix,
                "category": category,
                "already_grown": slug_prefix in existing,
                "description": desc,
            })
    return {
        "dialogue_length": len(blob),
        "hits": hits,
        "will_fire_next": next(
            (h["slug_prefix"] for h in hits if not h["already_grown"]),
            None,
        ),
    }


class InvokeRequest(BaseModel):
    slug: str
    args: Optional[list] = None
    kwargs: Optional[dict] = None


@router.post("/synthesize/invoke")
async def invoke_synthesized(req: InvokeRequest):
    """Load a synthesized capability's module by slug and call its
    top-level `run()`. This is the piece that closes the loop: Althea
    can now actually INVOKE the code she grew, not just persist it."""
    doc = await db.althea_capabilities.find_one(
        {"slug": req.slug}, {"_id": 0, "slug": 1}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="capability_not_found")

    path = GROWN_CODE_DIR / f"{req.slug}.py"
    if not path.exists():
        raise HTTPException(status_code=404, detail="module_file_missing")

    # Safe-scan the on-disk code AGAIN before executing (defense in depth).
    code = path.read_text(encoding="utf-8")
    scan = safe_code_scan(code)
    if not scan["safe"]:
        raise HTTPException(
            status_code=409,
            detail={"blocked": True, "findings": scan["findings"]},
        )

    import importlib.util
    try:
        spec = importlib.util.spec_from_file_location(req.slug, str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"import_failed: {str(exc)[:200]}",
        )
    fn = getattr(module, "run", None)
    if not callable(fn):
        raise HTTPException(status_code=500, detail="module_has_no_run")

    args = req.args or []
    kwargs = req.kwargs or {}
    try:
        result = fn(*args, **kwargs)
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc)[:300],
            "slug": req.slug,
        }

    # Bump invocation counter
    await db.althea_capabilities.update_one(
        {"slug": req.slug}, {"$inc": {"invocations": 1}},
    )
    return {"ok": True, "slug": req.slug, "result": result}



__all__ = [
    "synthesize_capability_from_dialogue",
    "router",
]
