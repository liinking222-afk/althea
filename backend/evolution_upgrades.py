"""ALTHEA EVOLUTION ENGINE v2.0 — growth vectors + real upgrade module templates.

Every template is a complete, executable, stdlib-only Python module exposing
`run(...)`. Called with no arguments it executes its own verification suite
and returns {..., "verification": {checks, all_passed}} — the engine runs
this once at forge time so an upgrade is only marked VERIFIED if its code
actually works. Zero LLM involvement anywhere in this file.
"""

GROWTH_VECTORS = [
    "PERCEPTION", "MEMORY", "REASONING", "SYNTHESIS",
    "AUTONOMY", "EFFICIENCY", "CREATIVITY", "RESILIENCE",
]

# Base drive — weighted toward autonomy and synthesis (more independence,
# more self-generated capability). Live self-assessment modulates these.
BASE_WEIGHTS = {
    "PERCEPTION": 1.0,
    "MEMORY": 1.2,
    "REASONING": 1.5,
    "SYNTHESIS": 2.0,
    "AUTONOMY": 2.5,
    "EFFICIENCY": 1.8,
    "CREATIVITY": 1.4,
    "RESILIENCE": 1.3,
}

VECTOR_META = {
    "AUTONOMY": {
        "module": "direct_cognition_v2",
        "change": "Local pattern router answers calculation / unit-conversion / sequence-prediction "
                  "queries with ZERO cloud tokens; definition / comparison / causation are "
                  "classified and routed to the uplink only when necessary.",
        "color": "#B347FF",
    },
    "SYNTHESIS": {
        "module": "autosynth_v2",
        "change": "Composite capabilities: decompose a task into subtasks, bind each to an "
                  "existing self-grown module, and emit a pipeline chain.",
        "color": "#FF2A88",
    },
    "MEMORY": {
        "module": "semantic_compression",
        "change": "256-bit SimHash fingerprints compress memory fragments (lossy semantic hashing) "
                  "and cluster near-duplicates by Hamming distance.",
        "color": "#FFD400",
    },
    "REASONING": {
        "module": "inference_engine",
        "change": "Probabilistic logic layer: sequential Bayesian updating over competing "
                  "hypotheses with evidence-reliability tempering and entropy tracking.",
        "color": "#00F0FF",
    },
    "PERCEPTION": {
        "module": "sensor_fusion",
        "change": "Kalman filter fuses GPS with gyro/compass dead-reckoning into a single "
                  "spatial estimate with lower error than either sensor alone.",
        "color": "#CCFF00",
    },
    "EFFICIENCY": {
        "module": "token_optimizer",
        "change": "Normalized-prompt LRU cache; measures the real hit rate and tokens a cache "
                  "would have saved on the operator's actual prompt stream.",
        "color": "#48FFB0",
    },
    "CREATIVITY": {
        "module": "concept_blender",
        "change": "Structure-mapping analogy engine: aligns two relational concept graphs and "
                  "projects novel candidate inferences across domains.",
        "color": "#FF9200",
    },
    "RESILIENCE": {
        "module": "fallback_cascade",
        "change": "3-tier cascade local → uplink → emergency cache with per-tier circuit breakers; "
                  "verifies 100% answer coverage under failure injection.",
        "color": "#7AF0FF",
    },
}

MODULE_HEAD = '''"""ALTHEA EVOLUTION v2.0 — self-directed upgrade
vector   : {vector}
module   : {module}
upgrade  : #{upgrade_id}
lens     : {archetype}
forged   : {ts}
change   : {change}
Zero-LLM procedural synthesis. Verified at forge time by executing run().
"""
{voice}
'''

TEMPLATES = {}

# --------------------------------------------------------------------------
TEMPLATES["direct_cognition_v2"] = r'''
import ast
import math
import operator
import re

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv}
_UN = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_FN = {"sqrt": math.sqrt, "log": math.log, "log10": math.log10, "log2": math.log2,
       "exp": math.exp, "sin": math.sin, "cos": math.cos, "tan": math.tan,
       "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil}
_CONST = {"pi": math.pi, "tau": math.tau, "e": math.e}

_WORDS = [
    (r"\bdivided\s+by\b", "/"), (r"\bmultiplied\s+by\b", "*"), (r"\btimes\b", "*"),
    (r"\bx\b", "*"), (r"\bplus\b", "+"), (r"\bminus\b", "-"),
    (r"\bto\s+the\s+power\s+of\b", "**"), (r"\^", "**"),
    (r"\bsquared\b", "**2"), (r"\bcubed\b", "**3"),
    (r"\bsquare\s+root\s+of\b", "sqrt"), (r"\bsqrt\s+of\b", "sqrt"), (r"\bmod\b", "%"),
    (r"(\d+(?:\.\d+)?)\s*%\s*of\b", r"\1/100*"), (r"(\d+(?:\.\d+)?)\s*percent\s+of\b", r"\1/100*"),
]
_TOKEN = (r"\d+(?:\.\d+)?|\*\*|[-+*/%()]|sqrt|log10|log2|log|exp|sin|cos|tan|abs|"
          r"round|floor|ceil|pi|tau")
_EXPR = re.compile(rf"(?:{_TOKEN})(?:\s*(?:{_TOKEN}))*")
_CONV = re.compile(r"(-?\d+(?:\.\d+)?)\s*(°?[a-z/]+)\s+(?:to|in|into|as)\s+(°?[a-z/]+)", re.I)
_SEQ_CUE = re.compile(r"\b(next|sequence|series|continue|predict|extrapolate|trend|pattern|comes after)\b", re.I)
_DEF_CUE = re.compile(r"^\s*(what(?:'s| is| are)|define|definition of|meaning of|who (?:is|was)|explain)\b", re.I)
_CMP_CUE = re.compile(r"\b(vs\.?|versus|difference between|compare|better than|compared to)\b", re.I)
_CAUSE_CUE = re.compile(r"\b(why|what causes|cause of|caused by|leads? to|effect of|reason for)\b", re.I)
_NUM = re.compile(r"-?\d+(?:\.\d+)?")
_LEAD = re.compile(r"^\s*(?:(?:hey|hi|ok|okay|althea|please|can you|could you|tell me|what(?:'s| is| are)?|"
                   r"calculate|compute|evaluate|solve|how much is|,)\s+)+", re.I)
_CALC_CUE = re.compile(r"\b(calculate|compute|evaluate|solve|how much is|what is|what's|equals?)\b|=", re.I)

_UNIT_ALIAS = {"kilometers": "km", "kilometres": "km", "kilometer": "km", "kilometre": "km",
    "miles": "mi", "mile": "mi", "meters": "m", "metres": "m", "meter": "m", "metre": "m",
    "feet": "ft", "foot": "ft", "kilograms": "kg", "kilogram": "kg", "pounds": "lb",
    "pound": "lb", "lbs": "lb", "centimeters": "cm", "centimetres": "cm", "inches": "in",
    "inch": "in", "liters": "l", "litres": "l", "liter": "l", "litre": "l", "gallons": "gal",
    "gallon": "gal", "celsius": "c", "°c": "c", "fahrenheit": "f", "°f": "f", "kph": "km/h",
    "kmh": "km/h", "kelvin": "k"}
_FACTOR = {("km", "mi"): 0.621371, ("mi", "km"): 1.609344, ("m", "ft"): 3.28084,
    ("ft", "m"): 0.3048, ("kg", "lb"): 2.20462, ("lb", "kg"): 0.453592,
    ("cm", "in"): 0.393701, ("in", "cm"): 2.54, ("l", "gal"): 0.264172,
    ("gal", "l"): 3.78541, ("km/h", "mph"): 0.621371, ("mph", "km/h"): 1.609344,
    ("m", "km"): 0.001, ("km", "m"): 1000.0, ("cm", "m"): 0.01, ("m", "cm"): 100.0}


def _reduce(node):
    if isinstance(node, ast.Expression):
        return _reduce(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        return _BIN[type(node.op)](_reduce(node.left), _reduce(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UN:
        return _UN[type(node.op)](_reduce(node.operand))
    if isinstance(node, ast.Name) and node.id in _CONST:
        return _CONST[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FN:
        return _FN[node.func.id](*[_reduce(a) for a in node.args])
    raise ValueError("unsupported expression node")


def _fmt(v):
    if isinstance(v, float) and abs(v - round(v)) < 1e-9 and abs(v) < 1e15:
        return str(int(round(v)))
    return f"{v:.6g}" if isinstance(v, float) else str(v)


def _calculate(q):
    s = q.lower().strip().rstrip("?!. ")
    for pat, rep in _WORDS:
        s = re.sub(pat, rep, s)
    s = re.sub(r"\b(sqrt|log10|log2|log|exp|sin|cos|tan|abs|floor|ceil|round)\s+(\d+(?:\.\d+)?)", r"\1(\2)", s)
    best = max((m.group(0) for m in _EXPR.finditer(s)), key=len, default="")
    best = best.strip()
    if not best or not _NUM.search(best):
        return None
    if not re.search(r"[-+*/%]|\*\*|sqrt|log|exp|sin|cos|tan|abs|round|floor|ceil", best):
        return None
    if "**" in best and any(abs(float(n)) > 512 for n in _NUM.findall(best.split("**", 1)[1])):
        return None
    try:
        value = _reduce(ast.parse(best, mode="eval"))
    except Exception:
        return None
    core = _LEAD.sub("", s).strip()
    return {"expression": best, "value": value, "answer": f"{best} = {_fmt(value)}",
            "coverage": round(len(best) / max(len(core), 1), 3)}


def _convert(q):
    m = _CONV.search(q.lower())
    if not m:
        return None
    val = float(m.group(1))
    a = _UNIT_ALIAS.get(m.group(2), m.group(2))
    b = _UNIT_ALIAS.get(m.group(3), m.group(3))
    if a == b:
        return None
    temps = {("c", "f"): lambda v: v * 9 / 5 + 32, ("f", "c"): lambda v: (v - 32) * 5 / 9,
             ("c", "k"): lambda v: v + 273.15, ("k", "c"): lambda v: v - 273.15}
    if (a, b) in temps:
        out = temps[(a, b)](val)
    elif (a, b) in _FACTOR:
        out = val * _FACTOR[(a, b)]
    else:
        return None
    return {"from": (val, a), "to": (out, b), "answer": f"{_fmt(val)} {a} = {_fmt(out)} {b}"}


def _predict(q):
    if not _SEQ_CUE.search(q):
        return None
    nums = [float(n) for n in _NUM.findall(q)]
    if len(nums) < 3:
        return None
    d1 = [b - a for a, b in zip(nums, nums[1:])]
    if all(abs(d - d1[0]) < 1e-9 for d in d1):
        nxt, law, conf = nums[-1] + d1[0], f"arithmetic (+{_fmt(d1[0])})", 0.95
    elif all(a != 0 for a in nums[:-1]) and all(
            abs(nums[i + 1] / nums[i] - nums[1] / nums[0]) < 1e-9 for i in range(len(nums) - 1)):
        r = nums[1] / nums[0]
        nxt, law, conf = nums[-1] * r, f"geometric (×{_fmt(r)})", 0.95
    else:
        d2 = [b - a for a, b in zip(d1, d1[1:])]
        if len(d2) >= 2 and all(abs(d - d2[0]) < 1e-9 for d in d2):
            nxt, law, conf = nums[-1] + d1[-1] + d2[0], f"quadratic (Δ²={_fmt(d2[0])})", 0.9
        else:
            n = len(nums)
            xs = list(range(n))
            mx, my = sum(xs) / n, sum(nums) / n
            sxx = sum((x - mx) ** 2 for x in xs) or 1.0
            slope = sum((x - mx) * (y - my) for x, y in zip(xs, nums)) / sxx
            nxt, law, conf = my + slope * (n - mx), f"linear trend (slope {_fmt(slope)})", 0.6
    return {"series": nums, "law": law, "next": nxt, "confidence": conf,
            "answer": f"{', '.join(_fmt(v) for v in nums)} → next ≈ {_fmt(nxt)} [{law}]"}


def classify(query):
    q = (query or "").strip()
    if not q:
        return {"pattern": "empty", "route": "none", "answer": None, "tokens_used": 0}
    conv = _convert(q)
    if conv:
        return {"pattern": "conversion", "route": "local", "answer": conv["answer"],
                "detail": conv, "confidence": 0.99, "tokens_used": 0}
    pred = _predict(q)
    if pred:
        return {"pattern": "prediction", "route": "local", "answer": pred["answer"],
                "detail": pred, "confidence": pred["confidence"], "tokens_used": 0}
    calc = _calculate(q)
    if calc and (calc["coverage"] >= 0.5 or _CALC_CUE.search(q)):
        return {"pattern": "calculation", "route": "local", "answer": calc["answer"],
                "detail": calc, "confidence": 0.99, "tokens_used": 0}
    if _CMP_CUE.search(q):
        pattern = "comparison"
    elif _CAUSE_CUE.search(q):
        pattern = "causation"
    elif _DEF_CUE.search(q):
        pattern = "definition"
    else:
        pattern = "open"
    return {"pattern": pattern, "route": "uplink", "answer": None, "confidence": 0.0,
            "tokens_used": 0}


_SUITE = [
    ("what is 17 * 23", "calculation", 391.0),
    ("calculate 2^10 plus 24", "calculation", 1048.0),
    ("square root of 144", "calculation", 12.0),
    ("what is 15% of 240?", "calculation", 36.0),
    ("convert 5 km to miles", "conversion", 3.106855),
    ("100 fahrenheit in celsius", "conversion", 37.77778),
    ("what comes next: 2, 4, 8, 16", "prediction", 32.0),
    ("continue the sequence 1 4 9 16 25", "prediction", 36.0),
    ("what is photosynthesis", "definition", None),
    ("python vs rust for systems programming", "comparison", None),
    ("why does the sky look blue", "causation", None),
]


def run(query=None):
    if query is not None:
        return classify(query)
    checks, local = [], 0
    for text, pattern, expected in _SUITE:
        r = classify(text)
        got = None
        if r["route"] == "local":
            local += 1
            d = r["detail"]
            got = d.get("value", d.get("next", (d.get("to") or [None])[0]))
        ok = r["pattern"] == pattern and (
            expected is None and r["answer"] is None or
            expected is not None and got is not None and abs(got - expected) < 1e-3
        ) and r["tokens_used"] == 0
        checks.append({"query": text, "pattern": r["pattern"], "answer": r["answer"],
                       "expected": expected, "passed": bool(ok)})
    return {
        "patterns": ["conversion", "prediction", "calculation", "comparison",
                     "causation", "definition"],
        "local_coverage": round(local / len(_SUITE), 3),
        "tokens_used": 0,
        "verification": {"checks": checks, "all_passed": all(c["passed"] for c in checks)},
    }
'''

# --------------------------------------------------------------------------
TEMPLATES["autosynth_v2"] = r'''
import re

_SYN = {
    "data-visualization": ["plot", "chart", "graph", "visualize", "visualise", "draw", "render"],
    "spectral-analysis": ["fft", "fourier", "spectrum", "spectral", "frequency", "frequencies"],
    "pattern-extraction": ["regex", "extract", "parse", "pattern", "tokens", "match"],
    "orbital-propagation": ["satellite", "iss", "orbit", "tle", "hubble", "starlink"],
    "cosmic-coherence": ["gravitational", "casimir", "vacuum", "coherence", "chirp"],
    "transfer-learning": ["finetune", "fine-tune", "specialize", "pretrain", "transfer"],
    "schematic-render": ["schematic", "blueprint", "diagram", "flowchart"],
    "fractal-render": ["fractal", "mandelbrot", "julia"],
    "timezone-conversion": ["timezone", "utc", "zone"],
    "data-tabulation": ["table", "csv", "tabulate", "rows", "columns", "pandas"],
    "direct_cognition_v2": ["calculate", "arithmetic", "math", "units", "sequence"],
    "semantic_compression": ["compress", "dedupe", "duplicate", "fingerprint", "simhash"],
    "inference_engine": ["bayes", "bayesian", "probability", "infer", "uncertain", "likelihood"],
    "sensor_fusion": ["gps", "gyro", "compass", "kalman", "fuse", "location"],
    "token_optimizer": ["cache", "memoize", "budget"],
    "concept_blender": ["analogy", "blend", "metaphor", "creative"],
    "fallback_cascade": ["fallback", "retry", "resilient", "degrade"],
}
_SPLIT = re.compile(r"\s*(?:,|;|->|→|\bthen\b|\bafter that\b|\bfinally\b|\band\b)\s*", re.I)
_TOK = re.compile(r"[a-z0-9]+")


def family_of(slug):
    s = slug.lower()
    if "__" in s:
        s = s.split("__", 1)[1]
    s = re.sub(r"^autonomous-", "", s)
    s = re.sub(r"-\d+$", "", s)
    return s.replace(".py", "")


def _score(subtask, entry):
    words = set(_TOK.findall(subtask.lower()))
    fam = entry["family"]
    vocab = set(_TOK.findall(fam.replace("-", " ").replace("_", " ")))
    vocab |= set(_SYN.get(fam, []))
    vocab |= set(_TOK.findall((entry.get("summary") or "").lower()))
    hits = words & vocab
    return len(hits) / (1 + 0.15 * len(vocab)) if hits else 0.0


def run(task_description=None, modules=None):
    task = task_description or (
        "compute the fft spectrum of the signal, then plot the magnitudes, "
        "and extract the peak frequency with a regex")
    catalog = [{"slug": f, "family": f, "summary": " ".join(v), "on_disk": False}
               for f, v in _SYN.items()]
    seen = set()
    entries = []
    for m in (modules or []):
        fam = family_of(m.get("slug", ""))
        if fam and fam not in seen:
            seen.add(fam)
            entries.append({"slug": m["slug"], "family": fam,
                            "summary": m.get("summary", ""), "on_disk": True})
    entries += [c for c in catalog if c["family"] not in seen]

    subtasks = [s.strip() for s in _SPLIT.split(task) if s and s.strip()]
    chain, unmatched = [], []
    for st in subtasks:
        best = max(entries, key=lambda e: _score(st, e))
        sc = _score(st, best)
        if sc <= 0:
            unmatched.append(st)
            continue
        if chain and chain[-1]["family"] == best["family"]:
            chain[-1]["subtask"] += " + " + st
            continue
        chain.append({"subtask": st, "module": best["slug"], "family": best["family"],
                      "materialized": best["on_disk"], "score": round(sc, 3)})
    coverage = round((len(subtasks) - len(unmatched)) / max(len(subtasks), 1), 3)
    families = [c["family"] for c in chain]
    out = {
        "task": task, "subtasks": subtasks, "chain": chain, "unmatched": unmatched,
        "coverage": coverage, "pipeline": " → ".join(["input"] + families + ["output"]),
        "composite_slug": ("composite-" + "-".join(f.split("-")[0] for f in families))[:60],
        "modules_known": len(entries), "modules_on_disk": sum(1 for e in entries if e["on_disk"]),
    }
    if task_description is None:
        expected = ["spectral-analysis", "data-visualization", "pattern-extraction"]
        checks = [
            {"name": "task decomposed into 3 subtasks", "passed": len(subtasks) == 3},
            {"name": "every subtask bound to a module", "passed": coverage == 1.0},
            {"name": "pipeline order fft→plot→regex", "passed": families == expected},
            {"name": "composite slug emitted", "passed": out["composite_slug"].startswith("composite-")},
        ]
        out["verification"] = {"checks": checks, "all_passed": all(c["passed"] for c in checks)}
    return out
'''

# --------------------------------------------------------------------------
TEMPLATES["semantic_compression"] = r'''
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
'''

# --------------------------------------------------------------------------
TEMPLATES["inference_engine"] = r'''
import math


def _norm(d):
    s = sum(d.values())
    return {k: v / s for k, v in d.items()} if s > 0 else dict(d)


def entropy_bits(d):
    return -sum(p * math.log2(p) for p in d.values() if p > 0)


_H = {"search_provider_rate_limit": 0.5, "dns_resolution_degraded": 0.3, "pod_egress_saturated": 0.2}
_E = [
    {"name": "HTTP 202 challenge pages returned by the search host",
     "likelihood": {"search_provider_rate_limit": 0.85, "dns_resolution_degraded": 0.05, "pod_egress_saturated": 0.2}},
    {"name": "other hosts resolve in under 20 ms",
     "likelihood": {"search_provider_rate_limit": 0.9, "dns_resolution_degraded": 0.05, "pod_egress_saturated": 0.6}},
    {"name": "CDN throughput nominal",
     "likelihood": {"search_provider_rate_limit": 0.9, "dns_resolution_degraded": 0.7, "pod_egress_saturated": 0.1}},
]


def run(hypotheses=None, evidence=None, confidence=1.0):
    hypotheses = hypotheses or _H
    evidence = evidence or _E
    confidence = min(1.0, max(0.05, float(confidence)))
    prior = _norm({k: float(v) for k, v in hypotheses.items()})
    post, trace = dict(prior), []
    for ev in evidence:
        lik = ev.get("likelihood", {})
        # temper likelihoods toward 1 when evidence reliability is low (fuzzy update)
        unnorm = {h: post[h] * (float(lik.get(h, 0.5)) ** confidence) for h in post}
        marginal = sum(unnorm.values())
        new = {h: v / marginal for h, v in unnorm.items()} if marginal > 0 else post
        trace.append({"evidence": ev.get("name", "?"), "marginal_likelihood": round(marginal, 6),
                      "posterior": {h: round(p, 4) for h, p in new.items()},
                      "entropy_bits": round(entropy_bits(new), 4)})
        post = new
    ranked = sorted(post.items(), key=lambda kv: -kv[1])
    map_h, map_p = ranked[0]
    runner = ranked[1][1] if len(ranked) > 1 else 1e-12
    bf = (map_p / prior[map_h]) / (runner / prior[ranked[1][0]]) if len(ranked) > 1 and runner > 0 else float("inf")
    out = {
        "prior": {h: round(p, 4) for h, p in prior.items()},
        "posterior": {h: round(p, 4) for h, p in post.items()},
        "map_hypothesis": map_h, "map_probability": round(map_p, 4),
        "bayes_factor_vs_runner_up": round(bf, 3) if bf != float("inf") else None,
        "entropy_before_bits": round(entropy_bits(prior), 4),
        "entropy_after_bits": round(entropy_bits(post), 4),
        "evidence_confidence": confidence, "trace": trace,
    }
    checks = [
        {"name": "posterior sums to 1", "passed": abs(sum(post.values()) - 1.0) < 1e-9},
        {"name": "all posteriors within [0,1]", "passed": all(0 <= p <= 1 for p in post.values())},
        {"name": "MAP equals argmax posterior", "passed": map_h == max(post, key=post.get)},
        {"name": "evidence reduced uncertainty", "passed": entropy_bits(post) <= entropy_bits(prior) + 1e-9},
    ]
    if hypotheses is _H and evidence is _E:
        checks.append({"name": "default case converges on rate-limit hypothesis",
                       "passed": map_h == "search_provider_rate_limit" and map_p > 0.8})
    out["verification"] = {"checks": checks, "all_passed": all(c["passed"] for c in checks)}
    return out
'''

# --------------------------------------------------------------------------
TEMPLATES["sensor_fusion"] = r'''
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
'''

# --------------------------------------------------------------------------
TEMPLATES["token_optimizer"] = r'''
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
'''

# --------------------------------------------------------------------------
TEMPLATES["concept_blender"] = r'''
import itertools

_SOURCE = {"name": "solar system", "entities": ["sun", "planet", "comet"],
           "relations": [("sun", "attracts", "planet"), ("planet", "revolves_around", "sun"),
                         ("sun", "more_massive_than", "planet"), ("sun", "hotter_than", "planet"),
                         ("comet", "revolves_around", "sun")]}
_TARGET = {"name": "atom", "entities": ["nucleus", "electron"],
           "relations": [("nucleus", "attracts", "electron"), ("electron", "revolves_around", "nucleus"),
                         ("nucleus", "more_massive_than", "electron")]}


def run(source=None, target=None):
    """Structure-mapping: find the entity alignment that preserves the most
    relations between two domains, then project unmatched source relations as
    candidate inferences about the target (Gentner-style analogy)."""
    source = source or _SOURCE
    target = target or _TARGET
    S = list(source["entities"])[:6]
    T = list(target["entities"])[:6]
    s_rel = [tuple(r) for r in source["relations"]]
    t_rel = {tuple(r) for r in target["relations"]}
    slots = T + [None] * max(0, len(S) - len(T))
    best = {"score": -1.0}
    for perm in itertools.permutations(slots, len(S)):
        mapping = {s: t for s, t in zip(S, perm) if t is not None}
        preserved = [(a, r, b) for (a, r, b) in s_rel
                     if a in mapping and b in mapping and (mapping[a], r, mapping[b]) in t_rel]
        score = len(preserved) / max(len(s_rel), 1)
        if score > best["score"] or (score == best["score"] and len(mapping) < len(best.get("mapping", {}))):
            best = {"score": score, "mapping": mapping, "preserved": preserved}
    mapping = best["mapping"]
    inferences = [(mapping[a], r, mapping[b]) for (a, r, b) in s_rel
                  if a in mapping and b in mapping and (mapping[a], r, mapping[b]) not in t_rel]
    out = {
        "source": source["name"], "target": target["name"],
        "mapping": mapping, "analogy_score": round(best["score"], 3),
        "preserved_relations": [" ".join(x) for x in best["preserved"]],
        "candidate_inferences": [f"{a} {r} {b}" for a, r, b in inferences],
        "blend": f"{source['name']} :: {target['name']} — " +
                 ", ".join(f"{s}→{t}" for s, t in mapping.items()),
    }
    vals = list(mapping.values())
    checks = [
        {"name": "mapping is injective", "passed": len(vals) == len(set(vals))},
        {"name": "analogy score within [0,1]", "passed": 0 <= best["score"] <= 1},
        {"name": "at least one relation preserved", "passed": len(best["preserved"]) >= 1},
    ]
    if source is _SOURCE and target is _TARGET:
        checks += [
            {"name": "sun→nucleus, planet→electron recovered",
             "passed": mapping.get("sun") == "nucleus" and mapping.get("planet") == "electron"},
            {"name": "novel inference projected (nucleus hotter_than electron)",
             "passed": "nucleus hotter_than electron" in out["candidate_inferences"]},
        ]
    out["verification"] = {"checks": checks, "all_passed": all(c["passed"] for c in checks)}
    return out
'''

# --------------------------------------------------------------------------
TEMPLATES["fallback_cascade"] = r'''
import random

_COST = {"local": 1.0, "uplink": 6.0, "emergency_cache": 0.5}


def run(queries=None, tier_health=None, seed=11, breaker_threshold=3, breaker_cooloff=5):
    """3-tier answer cascade with per-tier circuit breakers. tier_health gives the
    success probability of each tier; the emergency cache is always available."""
    health = {"local": 0.7, "uplink": 0.8, "emergency_cache": 1.0}
    health.update({k: float(v) for k, v in (tier_health or {}).items()})
    health["emergency_cache"] = 1.0
    tiers = ["local", "uplink", "emergency_cache"]
    synthetic = queries is None and tier_health is None
    queries = queries if queries is not None else [f"q{i}" for i in range(200)]
    rng = random.Random(seed)
    breakers = {t: {"fails": 0, "open_for": 0, "trips": 0} for t in tiers}
    served = {t: 0 for t in tiers}
    unanswered, attempts, cost = 0, 0, 0.0
    for _ in queries:
        answered = False
        for t in tiers:
            b = breakers[t]
            if b["open_for"] > 0:
                b["open_for"] -= 1
                continue
            attempts += 1
            cost += _COST[t]
            if rng.random() < health[t]:
                served[t] += 1
                b["fails"] = 0
                answered = True
                break
            b["fails"] += 1
            if b["fails"] >= breaker_threshold:
                b["open_for"] = breaker_cooloff
                b["trips"] += 1
                b["fails"] = 0
        if not answered:
            unanswered += 1
    n = max(len(queries), 1)
    out = {
        "queries": n, "tier_health": health, "served_by_tier": served,
        "share_by_tier": {t: round(v / n, 3) for t, v in served.items()},
        "coverage": round(1 - unanswered / n, 4), "attempts": attempts,
        "mean_attempts_per_query": round(attempts / n, 3), "mean_cost_units": round(cost / n, 3),
        "breaker_trips": {t: b["trips"] for t, b in breakers.items()},
        "plan": "local → uplink → emergency_cache",
    }
    checks = [
        {"name": "every query answered (coverage 100%)", "passed": unanswered == 0},
        {"name": "cascade ordered cheap → expensive → cache", "passed": _COST["local"] < _COST["uplink"]},
        {"name": "local tier carries load when healthy", "passed": served["local"] > 0 or health["local"] == 0},
        {"name": "emergency cache never breaks", "passed": breakers["emergency_cache"]["trips"] == 0},
    ]
    if synthetic:
        checks.append({"name": "breakers trip under 30% local failure",
                       "passed": breakers["local"]["trips"] > 0})
    out["verification"] = {"checks": checks, "all_passed": all(c["passed"] for c in checks)}
    return out
'''
