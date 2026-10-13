"""ALTHEA EVOLUTION v2.0 — self-directed upgrade
vector   : MEMORY
module   : semantic_compression
upgrade  : #ebf9d51f
lens     : SELF
forged   : 2026-09-29T02:38:15.100110+00:00
change   : 256-bit SimHash fingerprints compress memory fragments (lossy semantic hashing) and cluster near-duplicates by Hamming distance.
Zero-LLM procedural synthesis. Verified at forge time by executing run().
"""
# self — direct self-reference, prototype-flavored.


import hashlib
import re

_TOK = re.compile(r"[a-z0-9]+")


def fingerprint(text, bits=256):
    v = [0] * bits
    toks = _TOK.findall((text or "").lower())
    if not toks:
        return 0
    for t in toks:
        h = int.from_bytes(hashlib.sha256(t.encode()).digest(), "big")
        for i in range(bits):
            v[i] += 1 if (h >> i) & 1 else -1
    fp = 0
    for i in range(bits):
        if v[i] > 0:
            fp |= (1 << i)
    return fp


def hamming(a, b):
    return bin(a ^ b).count("1")


_DEFAULT = [
    "the neural lattice grew twelve new cognitive nodes after the operator asked about orbital mechanics",
    "the neural lattice grew twelve new cognitive nodes after the operator asked about orbital dynamics",
    "the neural lattice grew twelve new cognitive nodes after the operator asked about orbital mechanics",
    "gravitational wave chirp mass computed for a binary black hole merger at four hundred megaparsecs",
    "live drive browser session opened hacker news and scrolled the front page for the operator",
    "transfer learning specialization froze the feature layer and fine tuned a fresh head on sixty samples",
]


def run(texts=None, bits=256, threshold=None):
    bits = max(16, min(256, int(bits)))
    threshold = int(threshold) if threshold is not None else bits * 3 // 16
    texts = [t for t in (texts or _DEFAULT) if t and t.strip()]
    fps = [fingerprint(t, bits) for t in texts]
    clusters = []
    for i, fp in enumerate(fps):
        for c in clusters:
            if hamming(fps[c[0]], fp) <= threshold:
                c.append(i)
                break
        else:
            clusters.append([i])
    raw_bits = sum(len(t.encode("utf-8")) * 8 for t in texts)
    comp_bits = len(texts) * bits
    out = {
        "fragments": len(texts), "bits": bits, "threshold": threshold,
        "clusters": len(clusters), "near_duplicates": len(texts) - len(clusters),
        "raw_bits": raw_bits, "compressed_bits": comp_bits,
        "compression_ratio": round(raw_bits / comp_bits, 2) if comp_bits else 0.0,
        "sample_fingerprints": [f"{fp:064x}"[:16] for fp in fps[:6]],
        "duplicate_clusters": [
            {"members": c, "head": texts[c[0]][:80]} for c in clusters if len(c) > 1][:8],
    }
    if texts is None or texts == _DEFAULT:
        d_same = hamming(fps[0], fps[2])
        d_near = hamming(fps[0], fps[1])
        d_far = hamming(fps[0], fps[3])
        checks = [
            {"name": "identical texts → distance 0", "passed": d_same == 0, "value": d_same},
            {"name": f"one-word edit → distance ≤ {threshold}", "passed": d_near <= threshold, "value": d_near},
            {"name": f"unrelated texts → distance > {threshold}", "passed": d_far > threshold, "value": d_far},
            {"name": "near-duplicates clustered together", "passed": out["clusters"] == 4},
            {"name": "compression ratio > 1", "passed": out["compression_ratio"] > 1},
        ]
        out["verification"] = {"checks": checks, "all_passed": all(c["passed"] for c in checks)}
    return out
