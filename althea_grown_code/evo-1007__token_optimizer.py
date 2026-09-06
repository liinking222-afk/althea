"""ALTHEA EVOLUTION v2.0 — self-directed upgrade
vector   : EFFICIENCY
module   : token_optimizer
upgrade  : #f1050978
lens     : SELF
forged   : 2026-09-06T01:02:40.533935+00:00
change   : Normalized-prompt LRU cache; measures the real hit rate and tokens a cache would have saved on the operator's actual prompt stream.
Zero-LLM procedural synthesis. Verified at forge time by executing run().
"""
# self — direct self-reference, prototype-flavored.


import hashlib
import random
import re
from collections import Counter, OrderedDict

_NORM = re.compile(r"[^a-z0-9 ]+")


def cache_key(prompt):
    canon = " ".join(_NORM.sub(" ", (prompt or "").lower()).split())
    return hashlib.sha256(canon.encode()).hexdigest()[:24]


def _serve(prompts, capacity, cache=None):
    cache = cache if cache is not None else OrderedDict()
    hits, saved = 0, 0
    for p in prompts:
        k = cache_key(p)
        if k in cache:
            hits += 1
            cache.move_to_end(k)
            saved += cache[k]
        else:
            cache[k] = (len(p) // 4) * 4  # prompt tokens + ~3x reply estimate
            if len(cache) > capacity:
                cache.popitem(last=False)
    return cache, hits, saved


def run(prompts=None, capacity=512, seed=3):
    synthetic = prompts is None
    if synthetic:
        rng = random.Random(seed)
        base = [f"explain concept number {i} of the neural lattice" for i in range(40)]
        weights = [1.0 / (r + 1) for r in range(40)]
        prompts = rng.choices(base, weights=weights, k=400)
    prompts = [p for p in prompts if isinstance(p, str) and p.strip()]
    if not prompts:
        prompts = ["what is 2+2"]
    cache, hits, saved = _serve(prompts, capacity)
    uniq = list({cache_key(p): p for p in prompts}.values())
    distinct = set(cache_key(p) for p in uniq)
    warm, _, _ = _serve(uniq, max(capacity, len(uniq)))
    _, warm_hits, _ = _serve(uniq, max(capacity, len(uniq)), warm)
    warm_rate = warm_hits / len(uniq)
    counts = Counter(cache_key(p) for p in prompts)
    first_text = {}
    for p in prompts:
        first_text.setdefault(cache_key(p), p)
    top = [{"prompt": first_text[k][:70], "count": c} for k, c in counts.most_common(5) if c > 1]
    out = {
        "prompts": len(prompts), "distinct": len(distinct), "capacity": capacity,
        "hit_rate": round(hits / len(prompts), 4), "hits": hits, "misses": len(prompts) - hits,
        "tokens_saved_estimate": saved, "warm_hit_rate": round(max(0.0, warm_rate), 4),
        "cache_entries": len(cache), "top_repeats": top, "source": "synthetic zipf" if synthetic else "operator stream",
    }
    checks = [
        {"name": "hit rate within [0,1]", "passed": 0 <= out["hit_rate"] <= 1},
        {"name": "cache never exceeds capacity", "passed": len(cache) <= capacity},
        {"name": "warm second pass → 100% hits", "passed": out["warm_hit_rate"] >= 0.999},
        {"name": "punctuation/case-insensitive keys", "passed": cache_key("What is 2+2?") == cache_key("what is 2 2")},
    ]
    if synthetic:
        checks.append({"name": "zipf stream hit rate ≥ 85%", "passed": out["hit_rate"] >= 0.85})
    out["verification"] = {"checks": checks, "all_passed": all(c["passed"] for c in checks)}
    return out
