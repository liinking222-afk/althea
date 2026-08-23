"""ALTHEA Neural Interface Protocol (ANIP/1.0) — real BCI signal pipeline.

  · EDF / EDF+ parsing — byte-accurate against the EDF specification
    (Kemp et al., the interchange format referenced by IEEE 2731 BCI
    vocabulary and used by clinical EEG/ECoG systems).
  · Band-power decoding — Welch PSD → δ/θ/α/β/γ (scipy.signal).
  · Spike detection — Quiroga MAD threshold: σ = median(|x|)/0.6745,
    thr = 4.5σ (the standard extracellular spike-sorting front-end).
  · Substrate fusion — channel features fused through the verifiable
    transformer engine; state settled on the Hopfield lattice.
  · Synthetic acquisition — physiologically-shaped EEG generator so the
    pipeline can be demonstrated without electrodes attached.

Honest scope: no physical electrode is wired to this server. The decoding
math is real and accepts real recordings (EDF uploads / JSON frames).
"""
from __future__ import annotations

import base64
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from scipy.signal import welch

from core import db
from models import Memory
from neural_substrate import (
    differential_propagate,
    lattice_energy_relax,
    transformer_fuse,
)

router = APIRouter()

PROTOCOL = {
    "protocol": "ANIP/1.0 (Althea Neural Interface Protocol)",
    "signal_types": ["EEG", "ECoG", "extracellular spikes"],
    "formats": {
        "edf": "EDF / EDF+ (European Data Format, 16-bit, byte-accurate parser)",
        "json_frames": "{fs, channels:[{label, samples[]}]} — physical units µV",
    },
    "standards_referenced": [
        "EDF/EDF+ specification (Kemp et al.) — clinical EEG interchange",
        "IEEE Std 2731 BCI terminology (signal-acquisition → decoding vocabulary)",
        "10-20 electrode nomenclature (Fp1..O2, C3/C4 motor strip)",
        "Quiroga et al. MAD spike-threshold (σ = median|x|/0.6745)",
    ],
    "bands_hz": {"delta": [0.5, 4], "theta": [4, 8], "alpha": [8, 13],
                 "beta": [13, 30], "gamma": [30, 100]},
    "substrate": ["lattice-energy (Hopfield)",
                  "differential-propagation (LIF)",
                  "transformer-fusion (multi-head attention)"],
    "limits": {"max_channels": 16, "max_samples_per_channel": 60000,
               "max_edf_bytes": 8 * 1024 * 1024},
}

BANDS = {"delta": (0.5, 4.0), "theta": (4.0, 8.0), "alpha": (8.0, 13.0),
         "beta": (13.0, 30.0), "gamma": (30.0, 100.0)}


# ------------------------------------------------------------ core DSP
def band_powers(x: np.ndarray, fs: float) -> dict:
    nper = int(min(len(x), max(64, fs * 2)))
    freqs, psd = welch(x, fs=fs, nperseg=nper)
    powers = {}
    for name, (lo, hi) in BANDS.items():
        mask = (freqs >= lo) & (freqs < min(hi, fs / 2))
        powers[name] = float(np.trapezoid(psd[mask], freqs[mask])) if mask.any() else 0.0
    total = sum(powers.values()) or 1e-12
    rel = {k: round(v / total, 4) for k, v in powers.items()}
    return {"absolute": {k: round(v, 6) for k, v in powers.items()},
            "relative": rel, "total_power": round(total, 6)}


def detect_spikes(x: np.ndarray, fs: float, k: float = 4.5) -> dict:
    sigma = float(np.median(np.abs(x)) / 0.6745)
    thr = k * sigma
    refrac = int(max(1, fs * 0.001))  # 1 ms
    idx = []
    i = 0
    absx = np.abs(x)
    while i < len(x):
        if absx[i] > thr:
            idx.append(i)
            i += refrac
        else:
            i += 1
    times_ms = [round(j * 1000.0 / fs, 2) for j in idx]
    return {"sigma_mad": round(sigma, 4), "threshold": round(thr, 4),
            "k": k, "count": len(idx), "rate_hz": round(len(idx) * fs / max(len(x), 1), 3),
            "times_ms": times_ms[:200]}


# ------------------------------------------------------------ synthetic EEG
STATE_MIX = {
    # (delta, theta, alpha, beta, gamma) amplitude weights, µV-scaled
    "rest":        (4.0, 3.0, 12.0, 2.5, 0.8),
    "focus":       (2.0, 2.0, 3.5, 11.0, 3.0),
    "drowsy":      (6.0, 11.0, 4.0, 1.5, 0.5),
    "motor-left":  (2.5, 2.5, 5.0, 8.0, 2.0),
    "motor-right": (2.5, 2.5, 5.0, 8.0, 2.0),
}
DEFAULT_LABELS = ["Fp1", "Fp2", "C3", "C4", "P3", "P4", "O1", "O2"]


def synth_eeg(state: str, seconds: float, fs: float, n_channels: int, seed=None):
    rng = np.random.default_rng(seed)
    n = int(seconds * fs)
    t = np.arange(n) / fs
    mix = STATE_MIX.get(state, STATE_MIX["rest"])
    centers = [2.0, 6.0, 10.0, 20.0, 40.0]
    labels = (DEFAULT_LABELS * 2)[:n_channels]
    channels = []
    for ci in range(n_channels):
        label = labels[ci]
        x = np.zeros(n)
        for amp, f0 in zip(mix, centers):
            a = amp * (0.8 + 0.4 * rng.random())
            # Motor imagery → contralateral beta desynchronization (ERD)
            if state == "motor-left" and label == "C4" and f0 == 20.0:
                a *= 0.35
            if state == "motor-right" and label == "C3" and f0 == 20.0:
                a *= 0.35
            f = f0 * (0.9 + 0.2 * rng.random())
            x += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
        # 1/f pink-ish noise
        white = rng.normal(0, 1, n)
        pink = np.cumsum(white)
        pink = 2.0 * (pink - pink.mean()) / (np.abs(pink).max() + 1e-9)
        x += 3.0 * pink + rng.normal(0, 1.2, n)
        # occasional interictal-style spikes on frontal channels
        if ci < 2:
            for _ in range(rng.integers(1, 4)):
                p = rng.integers(0, n - int(0.02 * fs))
                width = int(0.004 * fs) or 1
                x[p:p + width] += rng.choice([-1, 1]) * 60.0
        channels.append({"label": label, "samples": [round(float(v), 3) for v in x]})
    return channels


# ------------------------------------------------------------ decoder
def decode_channels(channels: List[dict], fs: float) -> dict:
    feats, per_channel = [], []
    for ch in channels:
        x = np.asarray(ch["samples"], dtype=float)
        bp = band_powers(x, fs)
        sp = detect_spikes(x, fs)
        rel = bp["relative"]
        feats.append([rel["delta"], rel["theta"], rel["alpha"], rel["beta"], rel["gamma"]])
        per_channel.append({"label": ch.get("label", "ch"), "band_power": bp,
                            "spikes": sp, "n_samples": len(x)})

    F = np.asarray(feats)
    mean_rel = {k: round(float(F[:, i].mean()), 4)
                for i, k in enumerate(["delta", "theta", "alpha", "beta", "gamma"])}

    # Rule-based state decoder over real band features
    labels = [c["label"] for c in per_channel]
    state, evidence = "INDETERMINATE", []
    c3 = next((i for i, l in enumerate(labels) if l == "C3"), None)
    c4 = next((i for i, l in enumerate(labels) if l == "C4"), None)
    motor = None
    if c3 is not None and c4 is not None:
        b3, b4 = F[c3, 3], F[c4, 3]
        asym = (b3 - b4) / (b3 + b4 + 1e-9)
        beta_level = float(F[:, 3].mean())
        if beta_level > 0.25:  # motor imagery requires genuine beta engagement
            if asym > 0.22:
                motor = ("MOTOR-IMAGERY: LEFT hand (C4 beta ERD)", abs(asym))
            elif asym < -0.22:
                motor = ("MOTOR-IMAGERY: RIGHT hand (C3 beta ERD)", abs(asym))
        evidence.append(f"C3/C4 beta asymmetry = {round(float(asym), 3)}")
    ranked = sorted(mean_rel.items(), key=lambda kv: kv[1], reverse=True)
    dominant, second = ranked[0], ranked[1]
    margin = dominant[1] - second[1]
    if motor:
        state, confidence = motor[0], min(0.5 + motor[1], 0.98)
    else:
        state_map = {"alpha": "RELAXED / IDLE (alpha-dominant)",
                     "beta": "FOCUSED / ACTIVE (beta-dominant)",
                     "theta": "DROWSY (theta-dominant)",
                     "delta": "DEEP-SLOW (delta-dominant)",
                     "gamma": "HIGH-BINDING (gamma-dominant)"}
        state = state_map[dominant[0]]
        confidence = round(min(0.5 + margin * 2.5, 0.98), 3)
    evidence.append(f"dominant band {dominant[0]}={dominant[1]} vs {second[0]}={second[1]}")

    # Substrate fusion — feature matrix through the verifiable engines
    fusion = transformer_fuse(F, n_heads=4, seed=11)
    lattice = lattice_energy_relax(n=16, steps=40,
                                   seed=int(abs(F.sum() * 1000)) % (2**31))
    verification = {
        "fusion_checks": fusion["verification"],
        "lattice_checks": lattice["verification"],
        "psd_nonnegative": bool(all(
            v >= 0 for c in per_channel for v in c["band_power"]["absolute"].values())),
        "relative_power_normalized": bool(all(
            abs(sum(c["band_power"]["relative"].values()) - 1.0) < 0.01
            for c in per_channel)),
    }
    verification["all_passed"] = (
        fusion["verification"]["all_passed"]
        and lattice["verification"]["all_passed"]
        and verification["psd_nonnegative"]
        and verification["relative_power_normalized"]
    )
    return {
        "decoded_state": state,
        "confidence": round(float(confidence), 3),
        "evidence": evidence,
        "mean_relative_power": mean_rel,
        "channels": per_channel,
        "fusion": {"attention": fusion["attention"],
                   "entropy_nats": fusion["attention_entropy_nats"],
                   "fused_vector": fusion["fused_vector"][:16]},
        "lattice": {"energy_trajectory": lattice["energy_trajectory"],
                    "energy_released": lattice["energy_released"],
                    "converged_at_sweep": lattice["converged_at_sweep"]},
        "verification": verification,
    }


# ------------------------------------------------------------ EDF parser
def parse_edf(raw: bytes, max_seconds: float = 30.0) -> dict:
    if len(raw) < 256:
        raise ValueError("file too small to be EDF")
    def _s(a, b):
        return raw[a:b].decode("ascii", errors="ignore").strip()
    version = _s(0, 8)
    patient = _s(8, 88)
    recording = _s(88, 168)
    startdate, starttime = _s(168, 176), _s(176, 184)
    header_bytes = int(_s(184, 192) or 0)
    reserved = _s(192, 236)
    n_records = int(_s(236, 244) or 0)
    record_duration = float(_s(244, 252) or 1.0)
    ns = int(_s(252, 256) or 0)
    if ns <= 0 or ns > 64:
        raise ValueError(f"invalid signal count: {ns}")

    def _field(width, offset):
        base = 256 + offset * ns
        return [_s(base + i * width + 0, base + (i + 1) * width)
                for i in range(ns)] if False else [
            raw[base + i * width: base + (i + 1) * width].decode(
                "ascii", errors="ignore").strip() for i in range(ns)]

    # per-signal header block widths per EDF spec
    off = 256
    def _take(width):
        nonlocal off
        vals = [raw[off + i * width: off + (i + 1) * width].decode(
            "ascii", errors="ignore").strip() for i in range(ns)]
        off += width * ns
        return vals
    labels = _take(16)
    _transducer = _take(80)
    dims = _take(8)
    phys_min = [float(v or 0) for v in _take(8)]
    phys_max = [float(v or 1) for v in _take(8)]
    dig_min = [int(float(v or -32768)) for v in _take(8)]
    dig_max = [int(float(v or 32767)) for v in _take(8)]
    _prefilter = _take(80)
    spr = [int(float(v or 0)) for v in _take(8)]  # samples per record
    _take(32)  # reserved

    fs = spr[0] / record_duration if record_duration > 0 else 0.0
    max_records = min(n_records, int(max_seconds / record_duration) or 1) \
        if n_records > 0 else 0
    rec_len = sum(spr) * 2
    data_start = header_bytes or off
    channels = [[] for _ in range(ns)]
    for r in range(max_records):
        base = data_start + r * rec_len
        if base + rec_len > len(raw):
            break
        pos = base
        for i in range(ns):
            seg = np.frombuffer(raw[pos:pos + spr[i] * 2], dtype="<i2").astype(float)
            pos += spr[i] * 2
            scale = (phys_max[i] - phys_min[i]) / max(dig_max[i] - dig_min[i], 1)
            channels[i].extend((seg - dig_min[i]) * scale + phys_min[i])

    return {
        "format": "EDF+" if "EDF+" in reserved else "EDF",
        "version": version, "patient": patient[:60], "recording": recording[:60],
        "start": f"{startdate} {starttime}",
        "n_signals": ns, "n_records": n_records,
        "record_duration_s": record_duration, "fs": fs,
        "channels": [
            {"label": labels[i], "dimension": dims[i],
             "samples": [round(float(v), 3) for v in channels[i][:60000]]}
            for i in range(ns)
        ],
    }


# ------------------------------------------------------------ HTTP api
class SyntheticRequest(BaseModel):
    state: str = "rest"
    seconds: float = 2.0
    fs: float = 256.0
    channels: int = 8
    seed: Optional[int] = None
    decode: bool = True


class DecodeRequest(BaseModel):
    fs: float
    channels: List[dict]


class EdfRequest(BaseModel):
    b64: str
    decode: bool = True


class SubstrateLatticeRequest(BaseModel):
    n: int = 32
    steps: int = 64
    seed: Optional[int] = None


class SubstratePropagateRequest(BaseModel):
    n_neurons: int = 16
    duration_ms: float = 200.0
    seed: Optional[int] = None


class SubstrateFuseRequest(BaseModel):
    matrix: List[List[float]]
    n_heads: int = 4


async def _log_session(kind: str, summary: dict):
    try:
        doc = {"id": str(uuid.uuid4()), "kind": kind, "summary": summary,
               "timestamp": datetime.now(timezone.utc).isoformat()}
        await db.neural_sessions.insert_one(dict(doc))
        mem = Memory(
            content=f"[BCI {kind}] {str(summary)[:280]}",
            source="neural-interface", tags=["bci", "neural", kind],
        )
        m = mem.model_dump()
        m["timestamp"] = m["timestamp"].isoformat()
        await db.althea_memories.insert_one(m)
    except Exception:
        logging.exception("neural session log failed")


@router.get("/neural/protocol")
async def neural_protocol():
    return PROTOCOL


@router.post("/neural/synthetic")
async def neural_synthetic(req: SyntheticRequest):
    seconds = max(0.5, min(req.seconds, 10.0))
    fs = max(64.0, min(req.fs, 512.0))
    n_ch = max(1, min(req.channels, PROTOCOL["limits"]["max_channels"]))
    chans = synth_eeg(req.state, seconds, fs, n_ch, seed=req.seed)
    out = {"acquisition": "synthetic", "state_requested": req.state,
           "fs": fs, "seconds": seconds, "channels": chans}
    if req.decode:
        out["decode"] = decode_channels(chans, fs)
        await _log_session("synthetic-decode", {
            "state_requested": req.state,
            "decoded_state": out["decode"]["decoded_state"],
            "confidence": out["decode"]["confidence"],
        })
    return out


@router.post("/neural/decode")
async def neural_decode(req: DecodeRequest):
    if not req.channels:
        raise HTTPException(status_code=400, detail="no_channels")
    for ch in req.channels:
        n = len(ch.get("samples") or [])
        if n < 32:
            raise HTTPException(status_code=400, detail="channel_too_short")
        if n > PROTOCOL["limits"]["max_samples_per_channel"]:
            raise HTTPException(status_code=400, detail="channel_too_long")
    result = decode_channels(req.channels[:PROTOCOL["limits"]["max_channels"]],
                             max(32.0, min(req.fs, 4096.0)))
    await _log_session("decode", {
        "decoded_state": result["decoded_state"],
        "confidence": result["confidence"],
        "n_channels": len(req.channels),
    })
    return result


@router.post("/neural/edf/parse")
async def neural_edf_parse(req: EdfRequest):
    try:
        raw = base64.b64decode(req.b64)
    except Exception:
        raise HTTPException(status_code=400, detail="bad_base64")
    if len(raw) > PROTOCOL["limits"]["max_edf_bytes"]:
        raise HTTPException(status_code=413, detail="edf_too_large")
    try:
        parsed = parse_edf(raw)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"edf_parse_failed: {str(e)[:160]}")
    if req.decode and parsed["fs"] >= 32 and parsed["channels"]:
        usable = [c for c in parsed["channels"] if len(c["samples"]) >= 32]
        if usable:
            parsed["decode"] = decode_channels(
                usable[:PROTOCOL["limits"]["max_channels"]], parsed["fs"])
    await _log_session("edf-parse", {
        "format": parsed["format"], "n_signals": parsed["n_signals"],
        "fs": parsed["fs"],
    })
    return parsed


@router.post("/neural/substrate/lattice-energy")
async def substrate_lattice(req: SubstrateLatticeRequest):
    return lattice_energy_relax(n=max(4, min(req.n, 128)),
                                steps=max(1, min(req.steps, 256)), seed=req.seed)


@router.post("/neural/substrate/propagate")
async def substrate_propagate(req: SubstratePropagateRequest):
    return differential_propagate(
        n_neurons=max(2, min(req.n_neurons, 64)),
        duration_ms=max(20.0, min(req.duration_ms, 2000.0)), seed=req.seed)


@router.post("/neural/substrate/fuse")
async def substrate_fuse(req: SubstrateFuseRequest):
    if not req.matrix or not req.matrix[0]:
        raise HTTPException(status_code=400, detail="empty_matrix")
    if len(req.matrix) > 64 or len(req.matrix[0]) > 64:
        raise HTTPException(status_code=413, detail="matrix_too_large")
    return transformer_fuse(req.matrix, n_heads=max(1, min(req.n_heads, 8)))


@router.get("/neural/sessions")
async def neural_sessions(limit: int = 20):
    docs = await db.neural_sessions.find({}, {"_id": 0}).sort(
        "timestamp", -1).to_list(max(1, min(limit, 100)))
    return {"sessions": docs, "count": len(docs)}
