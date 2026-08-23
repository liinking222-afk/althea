"""ALTHEA Neural Substrate — verifiable computational engines.

Three REAL mathematical engines, each returning a verification block whose
invariants are actually checked at runtime (not asserted rhetorically):

  1. lattice_energy_relax()   — Hopfield lattice: E(s) = -1/2 sᵀWs - bᵀs.
     Asynchronous sign updates. Invariant: energy is monotonically
     non-increasing for symmetric W (Hopfield 1982 convergence theorem).

  2. differential_propagate() — leaky integrate-and-fire network:
     τ dV/dt = -(V - V_rest) + R·I(t), forward-Euler integration with
     refractory dynamics and exponential synaptic currents.
     Invariants: membrane bounds, refractory honored, dt stability.

  3. transformer_fuse()       — true scaled dot-product multi-head
     attention: softmax(QKᵀ/√d_k)V with residual + layer-norm.
     Invariants: every attention row sums to 1, no NaN, layernorm stats.

Every result carries a sha256 checksum so any run is reproducible and
externally auditable given the same seed.
"""
from __future__ import annotations

import hashlib
import json
import math

import numpy as np


def _checksum(payload) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def _round_list(arr, nd=4):
    return [round(float(x), nd) for x in np.asarray(arr).ravel()]


# ---------------------------------------------------------------- lattice
def lattice_energy_relax(n: int = 32, steps: int = 64, seed=None,
                         W=None, b=None, s0=None) -> dict:
    rng = np.random.default_rng(seed)
    if W is None:
        A = rng.normal(0.0, 1.0, (n, n))
        W = (A + A.T) / 2.0
        np.fill_diagonal(W, 0.0)
    else:
        W = np.asarray(W, dtype=float)
        n = W.shape[0]
    b = np.zeros(n) if b is None else np.asarray(b, dtype=float)
    if s0 is None:
        s = np.sign(rng.normal(size=n))
        s[s == 0] = 1.0
    else:
        s = np.sign(np.asarray(s0, dtype=float))
        s[s == 0] = 1.0

    def energy(state):
        return float(-0.5 * state @ W @ state - b @ state)

    traj = [energy(s)]
    flips = 0
    converged_at = None
    for step in range(int(steps)):
        changed = False
        for i in rng.permutation(n):
            h = float(W[i] @ s + b[i])
            new = 1.0 if h >= 0 else -1.0
            if new != s[i]:
                s[i] = new
                changed = True
                flips += 1
        traj.append(energy(s))
        if not changed:
            converged_at = step + 1
            break

    diffs = np.diff(traj)
    checks = [
        {"name": "W_symmetric", "passed": bool(np.allclose(W, W.T, atol=1e-9))},
        {"name": "energy_monotone_nonincreasing",
         "passed": bool(np.all(diffs <= 1e-9)),
         "max_violation": float(max(0.0, diffs.max())) if len(diffs) else 0.0},
        {"name": "fixed_point_reached", "passed": converged_at is not None},
        {"name": "states_bipolar",
         "passed": bool(np.all(np.isin(s, (-1.0, 1.0))))},
    ]
    out = {
        "engine": "lattice-energy",
        "n": int(n),
        "energy_trajectory": _round_list(traj),
        "initial_energy": round(traj[0], 4),
        "final_energy": round(traj[-1], 4),
        "energy_released": round(traj[0] - traj[-1], 4),
        "spin_flips": int(flips),
        "converged_at_sweep": converged_at,
        "final_state": _round_list(s, 0),
    }
    out["verification"] = {
        "checks": checks,
        "all_passed": all(c["passed"] for c in checks),
        "checksum": _checksum(out),
    }
    return out


# ---------------------------------------------------- differential propagation
def differential_propagate(n_neurons: int = 16, duration_ms: float = 200.0,
                           dt_ms: float = 0.1, seed=None,
                           drive: float = 1.9) -> dict:
    rng = np.random.default_rng(seed)
    n = int(n_neurons)
    tau, v_rest, v_th, v_reset = 20.0, -65.0, -50.0, -70.0
    r_m, tau_syn, refrac_ms = 10.0, 5.0, 2.0

    W = rng.normal(0.0, 0.6, (n, n)) * (rng.random((n, n)) < 0.2)
    np.fill_diagonal(W, 0.0)

    steps = int(duration_ms / dt_ms)
    V = np.full(n, v_rest)
    refr = np.zeros(n)
    i_syn = np.zeros(n)
    i_ext = drive + rng.normal(0.0, 0.25, n)
    spikes = [[] for _ in range(n)]
    mean_v_trace = []
    refractory_violations = 0
    v_min_seen, v_max_seen = float(V.min()), float(V.max())

    for k in range(steps):
        t = k * dt_ms
        i_syn *= math.exp(-dt_ms / tau_syn)
        active = refr <= 0.0
        dV = (-(V - v_rest) + r_m * (i_ext + i_syn)) / tau
        V = np.where(active, V + dt_ms * dV, V)
        fired = (V >= v_th) & active
        if fired.any():
            for i in np.flatnonzero(fired):
                if spikes[i] and (t - spikes[i][-1]) < refrac_ms - 1e-9:
                    refractory_violations += 1
                spikes[i].append(round(t, 2))
            i_syn = i_syn + W[:, fired].sum(axis=1)
            V[fired] = v_reset
            refr[fired] = refrac_ms
        refr = np.maximum(refr - dt_ms, 0.0)
        v_min_seen = min(v_min_seen, float(V.min()))
        v_max_seen = max(v_max_seen, float(V.max()))
        if k % max(1, steps // 200) == 0:
            mean_v_trace.append(round(float(V.mean()), 3))

    total_spikes = sum(len(s) for s in spikes)
    rates = [round(len(s) * 1000.0 / duration_ms, 2) for s in spikes]
    checks = [
        {"name": "dt_stability(dt<tau/10)", "passed": dt_ms < tau / 10.0},
        {"name": "membrane_bounded",
         "passed": (v_min_seen >= v_reset - 25.0) and (v_max_seen <= v_th + 5.0),
         "v_min": round(v_min_seen, 2), "v_max": round(v_max_seen, 2)},
        {"name": "refractory_honored", "passed": refractory_violations == 0},
        {"name": "network_active", "passed": total_spikes > 0},
    ]
    out = {
        "engine": "differential-propagation",
        "model": "leaky-integrate-and-fire (forward Euler)",
        "n_neurons": n,
        "duration_ms": duration_ms,
        "dt_ms": dt_ms,
        "total_spikes": int(total_spikes),
        "mean_rate_hz": round(float(np.mean(rates)), 2),
        "rates_hz": rates,
        "spike_raster": [s[:60] for s in spikes],
        "mean_v_trace": mean_v_trace,
    }
    out["verification"] = {
        "checks": checks,
        "all_passed": all(c["passed"] for c in checks),
        "checksum": _checksum(out),
    }
    return out


# ------------------------------------------------------- transformer fusion
def _softmax_rows(x):
    x = x - x.max(axis=-1, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=-1, keepdims=True)


def _layer_norm(x, eps=1e-6):
    mu = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    return (x - mu) / np.sqrt(var + eps)


def transformer_fuse(X, n_heads: int = 4, d_model: int = 32, seed: int = 7) -> dict:
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X.reshape(1, -1)
    n_tok, d_in = X.shape
    rng = np.random.default_rng(seed)

    W_in = rng.normal(0.0, 1.0 / math.sqrt(max(d_in, 1)), (d_in, d_model))
    H = X @ W_in
    d_k = d_model // n_heads
    head_outs, att_maps = [], []
    for _ in range(n_heads):
        Wq = rng.normal(0.0, 1.0 / math.sqrt(d_model), (d_model, d_k))
        Wk = rng.normal(0.0, 1.0 / math.sqrt(d_model), (d_model, d_k))
        Wv = rng.normal(0.0, 1.0 / math.sqrt(d_model), (d_model, d_k))
        Q, K, V = H @ Wq, H @ Wk, H @ Wv
        A = _softmax_rows(Q @ K.T / math.sqrt(d_k))
        head_outs.append(A @ V)
        att_maps.append(A)
    concat = np.concatenate(head_outs, axis=-1)
    W_o = rng.normal(0.0, 1.0 / math.sqrt(d_model), (d_model, d_model))
    out = _layer_norm(H + concat @ W_o)

    mean_att = np.mean(att_maps, axis=0)
    row_sums = mean_att.sum(axis=-1)
    # attention entropy (nats) — how spread the fusion is
    ent = float(-(mean_att * np.log(mean_att + 1e-12)).sum(axis=-1).mean())
    checks = [
        {"name": "softmax_rows_sum_to_1",
         "passed": bool(np.allclose(row_sums, 1.0, atol=1e-9)),
         "max_err": float(np.abs(row_sums - 1.0).max())},
        {"name": "no_nan_or_inf", "passed": bool(np.isfinite(out).all())},
        {"name": "layernorm_zero_mean",
         "passed": bool(np.allclose(out.mean(axis=-1), 0.0, atol=1e-6))},
        {"name": "shape_preserved", "passed": out.shape == (n_tok, d_model)},
    ]
    res = {
        "engine": "transformer-fusion",
        "n_tokens": int(n_tok),
        "d_in": int(d_in),
        "d_model": int(d_model),
        "n_heads": int(n_heads),
        "attention_entropy_nats": round(ent, 4),
        "attention": [[round(float(v), 4) for v in row] for row in mean_att],
        "fused_vector": _round_list(out.mean(axis=0)),
    }
    res["verification"] = {
        "checks": checks,
        "all_passed": all(c["passed"] for c in checks),
        "checksum": _checksum(res),
    }
    return res


__all__ = ["lattice_energy_relax", "differential_propagate", "transformer_fuse"]
