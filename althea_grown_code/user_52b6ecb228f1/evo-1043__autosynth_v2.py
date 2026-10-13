"""ALTHEA EVOLUTION v2.0 — self-directed upgrade
vector   : SYNTHESIS
module   : autosynth_v2
upgrade  : #b924e641
lens     : SELF
forged   : 2026-09-06T01:16:03.332220+00:00
change   : Composite capabilities: decompose a task into subtasks, bind each to an existing self-grown module, and emit a pipeline chain.
Zero-LLM procedural synthesis. Verified at forge time by executing run().
"""
# self — direct self-reference, prototype-flavored.


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
