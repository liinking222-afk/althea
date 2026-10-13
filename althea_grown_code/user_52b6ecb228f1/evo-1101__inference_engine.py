"""ALTHEA EVOLUTION v2.0 — self-directed upgrade
vector   : REASONING
module   : inference_engine
upgrade  : #d5d3fa12
lens     : SELF
forged   : 2026-09-07T01:18:47.004681+00:00
change   : Probabilistic logic layer: sequential Bayesian updating over competing hypotheses with evidence-reliability tempering and entropy tracking.
Zero-LLM procedural synthesis. Verified at forge time by executing run().
"""
# self — direct self-reference, prototype-flavored.


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
