"""AUTOSYNTH — Tabular Analysis
Category: pandas
Generated: 2026-08-27T21:44:12.947604+00:00
Rationale: Detected in recent dialogue: 'tabular-analysis' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

import statistics


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
