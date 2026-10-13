"""ALTHEA EVOLUTION v2.0 — self-directed upgrade
vector   : PERCEPTION
module   : sensor_fusion
upgrade  : #50da60ec
lens     : SELF
forged   : 2026-09-06T01:24:27.368700+00:00
change   : Kalman filter fuses GPS with gyro/compass dead-reckoning into a single spatial estimate with lower error than either sensor alone.
Zero-LLM procedural synthesis. Verified at forge time by executing run().
"""
# self — direct self-reference, prototype-flavored.


import math
import random


def _rmse(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / max(len(a), 1))


def run(samples=None, seed=7, dt=1.0, gps_sigma=8.0, dr_sigma=2.0, drift_rate=0.4, q=0.05):
    """Fuse GPS fixes with gyro/compass dead-reckoning (heading x speed integrated)
    through a constant-velocity Kalman filter. samples: [{gps, dr, truth?}, ...]."""
    rng = random.Random(seed)
    truth = None
    if samples is None:
        n, v = 120, 1.5
        truth, gps, dr, drift = [], [], [], 0.0
        for k in range(n):
            p = k * dt * v
            truth.append(p)
            gps.append(p + rng.gauss(0, gps_sigma))
            drift += rng.gauss(0, drift_rate)
            dr.append(p + drift + rng.gauss(0, dr_sigma))
    else:
        gps = [float(s["gps"]) for s in samples]
        dr = [float(s.get("dr", s["gps"])) for s in samples]
        if all("truth" in s for s in samples):
            truth = [float(s["truth"]) for s in samples]
        n = len(gps)
    x = [gps[0], 0.0]
    P = [[gps_sigma ** 2, 0.0], [0.0, 10.0]]
    Q = [[q * dt ** 3 / 3, q * dt ** 2 / 2], [q * dt ** 2 / 2, q * dt]]
    est, gains = [], []
    for k in range(n):
        xp = [x[0] + dt * x[1], x[1]]
        p00 = P[0][0] + dt * (P[1][0] + P[0][1]) + dt * dt * P[1][1] + Q[0][0]
        p01 = P[0][1] + dt * P[1][1] + Q[0][1]
        p11 = P[1][1] + Q[1][1]
        Pp = [[p00, p01], [p01, p11]]
        for z, R in ((gps[k], gps_sigma ** 2), (dr[k], dr_sigma ** 2 + drift_rate ** 2 * (k + 1))):
            S = Pp[0][0] + R
            K = [Pp[0][0] / S, Pp[1][0] / S]
            y = z - xp[0]
            xp = [xp[0] + K[0] * y, xp[1] + K[1] * y]
            Pp = [[(1 - K[0]) * Pp[0][0], (1 - K[0]) * Pp[0][1]],
                  [Pp[1][0] - K[1] * Pp[0][0], Pp[1][1] - K[1] * Pp[0][1]]]
            gains.append(K[0])
        x, P = xp, Pp
        est.append(x[0])
    out = {
        "samples": n, "fused_track": [round(e, 3) for e in est[-10:]],
        "velocity_estimate": round(x[1], 4), "final_covariance": [[round(c, 5) for c in r] for r in P],
        "mean_gps_gain": round(sum(gains[0::2]) / max(len(gains[0::2]), 1), 4),
        "mean_dr_gain": round(sum(gains[1::2]) / max(len(gains[1::2]), 1), 4),
        "sensors": ["gps", "gyro+compass dead-reckoning"],
    }
    checks = [
        {"name": "covariance positive-definite", "passed": P[0][0] > 0 and P[1][1] > 0 and P[0][0] * P[1][1] - P[0][1] ** 2 > 0},
        {"name": "kalman gains within (0,1)", "passed": all(0 < g < 1 for g in gains)},
    ]
    if truth is not None:
        e_gps, e_dr, e_f = _rmse(gps, truth), _rmse(dr, truth), _rmse(est, truth)
        out.update({"rmse_gps": round(e_gps, 3), "rmse_dead_reckoning": round(e_dr, 3),
                    "rmse_fused": round(e_f, 3),
                    "error_reduction_pct": round(100 * (1 - e_f / min(e_gps, e_dr)), 1)})
        checks += [
            {"name": "fused error < GPS-only error", "passed": e_f < e_gps},
            {"name": "fused error < dead-reckoning error", "passed": e_f < e_dr},
        ]
        if samples is None:
            checks.append({"name": "velocity recovered within 30%", "passed": abs(x[1] - 1.5) < 0.45})
    out["verification"] = {"checks": checks, "all_passed": all(c["passed"] for c in checks)}
    return out
