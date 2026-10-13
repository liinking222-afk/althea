"""ALTHEA EVOLUTION v2.0 — self-directed upgrade
vector   : CREATIVITY
module   : concept_blender
upgrade  : #45bfb683
lens     : SELF
forged   : 2026-09-11T06:37:19.562683+00:00
change   : Structure-mapping analogy engine: aligns two relational concept graphs and projects novel candidate inferences across domains.
Zero-LLM procedural synthesis. Verified at forge time by executing run().
"""
# self — direct self-reference, prototype-flavored.


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
