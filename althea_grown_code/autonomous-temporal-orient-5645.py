"""AUTOSYNTH — Temporal Orient
Category: chronology
Generated: 2026-08-23T06:14:05.346007+00:00
Rationale: Detected in recent dialogue: 'temporal-orient' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

from datetime import datetime, timezone


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
