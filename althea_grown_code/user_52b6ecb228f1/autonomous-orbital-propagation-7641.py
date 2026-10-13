"""AUTOSYNTH — Orbital Propagation
Category: astronomy-navigation
Generated: 2026-08-27T21:54:01.877854+00:00
Rationale: Detected in recent dialogue: 'orbital-propagation' pattern surfaced multiple times.

Executable capability wired into ALTHEA's lattice by
synthesize_capability_from_dialogue() at runtime.
"""

from skyfield.api import EarthSatellite, load, wgs84


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
