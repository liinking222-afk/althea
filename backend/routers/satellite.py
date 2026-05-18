"""Satellite uplink — simulated low-earth-orbit mesh data.

Returns deterministic-ish satellite positions, signal strength, and
constellation membership so the UI can render a starlink-style orbit map.
"""
import math
import random
import time
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()

CONSTELLATIONS = [
    {"name": "ALTHEA-NORTH", "count": 14, "color": "#CCFF00", "altitude_km": 550},
    {"name": "ALTHEA-SOUTH", "count": 12, "color": "#00F0FF", "altitude_km": 580},
    {"name": "MIRROR-MESH", "count": 8, "color": "#FF2A88", "altitude_km": 610},
]


@router.get("/satellite/feed")
async def satellite_feed():
    """Return current satellite mesh state. Positions evolve with time so the UI
    can animate orbits, but the constellation membership is stable."""
    t = time.time()
    sats = []
    for c in CONSTELLATIONS:
        for i in range(c["count"]):
            # Stable seed per (constellation, index)
            seed_h = abs(hash((c["name"], i))) % 1000
            rng = random.Random(seed_h)
            inclination = rng.uniform(0.5, 1.5)  # rad
            phase = rng.uniform(0, math.pi * 2)
            period = 90 + rng.uniform(-15, 15)  # minutes
            angle = phase + (t / (period * 60)) * math.pi * 2
            # convert to (lat, lon)
            lat = math.degrees(math.asin(math.sin(inclination) * math.sin(angle)))
            lon = ((math.degrees(math.atan2(math.cos(inclination) * math.sin(angle), math.cos(angle))) + 180) % 360) - 180
            # signal: higher near apex
            signal = 0.6 + 0.4 * abs(math.sin(angle * 1.3 + seed_h * 0.01))
            sats.append({
                "id": f"{c['name']}-{i:02d}",
                "constellation": c["name"],
                "color": c["color"],
                "altitude_km": c["altitude_km"],
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "signal": round(signal, 3),
                "phase": round(angle % (math.pi * 2), 3),
            })

    # Aggregate metrics
    total = len(sats)
    avg_signal = round(sum(s["signal"] for s in sats) / max(total, 1), 3)
    locked = [s for s in sats if s["signal"] > 0.85]
    uplink_bps = int(2_500_000 + math.sin(t / 7) * 600_000 + len(locked) * 18_000)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "satellites": sats,
        "constellations": CONSTELLATIONS,
        "metrics": {
            "total": total,
            "locked": len(locked),
            "avg_signal": avg_signal,
            "uplink_bps": uplink_bps,
            "downlink_bps": int(uplink_bps * 1.8),
            "mesh_integrity": round(0.86 + math.sin(t / 11) * 0.07, 3),
        },
    }
