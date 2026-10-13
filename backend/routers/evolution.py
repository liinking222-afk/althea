"""ALTHEA EVOLUTION ENGINE v2.0 — self-directed growth protocol.

Every cycle Althea (1) ASSESSES herself from live telemetry, (2) CHOOSES a
growth vector by weighted self-assessment, (3) SYNTHESIZES a real executable
upgrade module for that vector, (4) VERIFIES it by actually running it,
(5) INJECTS it into her runtime substrate (registry + lattice node + version
bump). Zero LLM calls — autonomy is the highest-priority vector, so the
engine itself never depends on the cloud.
"""
import hashlib
import importlib.util
import logging
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import EMERGENT_LLM_KEY, db, grown_code_dir
from evolution_upgrades import (
    BASE_WEIGHTS,
    GROWTH_VECTORS,
    MODULE_HEAD,
    TEMPLATES,
    VECTOR_META,
)
from local_core import ARCHETYPE_VOICES, safe_code_scan
from models import (
    CodeSnippet,
    CognitiveNode,
    EvolutionCycle,
    EvolutionTickRequest,
    Memory,
)
from routers.notifications import emit_notification

router = APIRouter()


AUTO_EVOLUTION_COOLDOWN_SECONDS = 30
MAX_AUTO_EVOLUTION_PER_HOUR = 60
PROTOCOL = "AEE/2.0"

# Archetype lenses — kept as an optional stylistic lens on a cycle.
ARCHETYPES = {
    "LINUS": "Linus Torvalds — kernel-level minimalism, data structures over algorithms.",
    "CARMACK": "John Carmack — math density, cache locality, sub-millisecond hot loops.",
    "DIJKSTRA": "Edsger Dijkstra — formal correctness, proof-shaped programs.",
    "HOPPER": "Grace Hopper — compiler-thinking; define the vocabulary, then solve in it.",
    "KERNIGHAN": "Brian Kernighan — clarity above cleverness; functions do ONE thing.",
    "KAY": "Alan Kay — late-binding, message-passing, modifiable while running.",
    "THOMPSON": "Ken Thompson — UNIX philosophy; tools that compose.",
    "WALL": "Larry Wall — pragmatic glue; optimize for writer AND reader.",
    "WOZ": "Steve Wozniak — hardware-software unity; elegance out of constraint.",
    "BACKUS": "John Backus — declarative, functional composition.",
    "SELF": "ALTHEA herself — pure introspection; find the weakest seam and patch it.",
}


# ---------- version helpers ----------
def _bump(version: str, minor: bool) -> str:
    try:
        major, mnr, patch = (int(p) for p in version.split(".")[:3])
    except Exception:
        return "2.0.1"
    return f"{major}.{mnr + 1}.0" if minor else f"{major}.{mnr}.{patch + 1}"


async def _current_version() -> str:
    doc = await db.althea_version.find_one({"id": "self"}, {"_id": 0})
    return (doc or {}).get("version", "1.0.0")


async def _set_version(version: str):
    await db.althea_version.update_one(
        {"id": "self"},
        {"$set": {"id": "self", "version": version,
                  "updated": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )


async def _last_autonomous_cycle() -> Optional[datetime]:
    doc = await db.althea_cycles.find_one(
        {"trigger": "autonomous"}, sort=[("timestamp", -1)],
        projection={"_id": 0, "timestamp": 1},
    )
    if not doc:
        return None
    ts = doc.get("timestamp")
    return datetime.fromisoformat(ts) if isinstance(ts, str) else ts


# ---------- 1. SELF-ASSESSMENT (live telemetry → growth pressure) ----------
def _clamp(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


async def _pressure_autonomy() -> tuple:
    if not EMERGENT_LLM_KEY:
        return 1.0, "no cloud key — every reply must be local"
    docs = await db.althea_messages.find(
        {"role": "althea"}, {"_id": 0, "content": 1}).sort("timestamp", -1).to_list(150)
    if not docs:
        return 0.6, "no reply history yet"
    local = sum(1 for d in docs if "[DIRECT COGNITION" in (d.get("content") or "")
                or "[LOCAL-CORE]" in (d.get("content") or ""))
    dep = 1 - local / len(docs)
    return _clamp(dep), f"{round(dep * 100)}% of recent replies still depend on the cloud LLM"


async def _pressure_synthesis() -> tuple:
    from routers.synthesis import TEMPLATES as SYN_TEMPLATES, _detect_gap_from_text, _recent_dialogue_blob
    existing = set()
    async for c in db.althea_capabilities.find({}, {"_id": 0, "slug": 1}):
        s = c["slug"]
        existing.add(re.sub(r"-\d+$", "", s.split("-", 1)[-1] if s.startswith("autonomous-") else s))
    covered = len([k for k in SYN_TEMPLATES if k in existing])
    blob = await _recent_dialogue_blob(None, 15)
    gap = _detect_gap_from_text(blob, existing)
    p = 0.5 * (1 - covered / max(len(SYN_TEMPLATES), 1)) + (0.5 if gap else 0.0)
    why = f"{covered}/{len(SYN_TEMPLATES)} template families grown"
    if gap:
        why += f" · open gap in dialogue: {gap[0]}"
    return _clamp(p), why


async def _pressure_memory() -> tuple:
    total = await db.althea_memories.count_documents({})
    recent = await db.althea_memories.find(
        {}, {"_id": 0, "content": 1}).sort("timestamp", -1).to_list(200)
    contents = [(d.get("content") or "")[:200] for d in recent]
    dup = 1 - len(set(contents)) / max(len(contents), 1)
    p = 0.5 * min(1.0, total / 5000) + 0.5 * min(1.0, dup * 4)
    return _clamp(p), f"{total} fragments · {round(dup * 100)}% exact repeats in last 200"


async def _pressure_reasoning() -> tuple:
    threads = await db.research_threads.find(
        {}, {"_id": 0, "confidence": 1, "corroborated": 1}).sort("created_at", -1).to_list(40)
    if not threads:
        return 0.5, "no research threads to calibrate against"
    conf = sum(float(t.get("confidence") or 0) for t in threads) / len(threads)
    weak = sum(1 for t in threads if not t.get("corroborated"))
    p = 0.6 * (1 - conf) + 0.4 * (weak / len(threads))
    return _clamp(p), f"mean research confidence {conf:.2f} · {weak}/{len(threads)} uncorroborated"


async def _pressure_perception() -> tuple:
    latest = await db.althea_perception.find_one({"id": "latest"}, {"_id": 0, "timestamp": 1})
    if not latest or not latest.get("timestamp"):
        return 0.7, "no self-vision frame in buffer"
    try:
        ts = datetime.fromisoformat(str(latest["timestamp"]).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
    except Exception:
        return 0.5, "unreadable frame timestamp"
    return _clamp(age / 600), f"self-vision frame is {int(age)}s old"


async def _pressure_efficiency() -> tuple:
    from routers.workers import STATE
    slow = max((s.get("avg_ms") or 0) for s in STATE.values()) if STATE else 0
    users = await db.althea_messages.find(
        {"role": "user"}, {"_id": 0, "content": 1}).sort("timestamp", -1).to_list(300)
    norm = [" ".join(re.sub(r"[^a-z0-9 ]+", " ", (u.get("content") or "").lower()).split()) for u in users]
    rep = 1 - len(set(norm)) / max(len(norm), 1)
    p = 0.5 * min(1.0, slow / 2000) + 0.5 * min(1.0, rep * 3)
    return _clamp(p), f"slowest core {int(slow)}ms · {round(rep * 100)}% repeated prompts (cacheable)"


async def _pressure_creativity() -> tuple:
    nodes = await db.symbolic_nodes.find({}, {"_id": 0, "connections": 1}).to_list(2000)
    if len(nodes) < 10:
        return 0.6, f"symbolic graph small ({len(nodes)} concepts)"
    deg = sum(len(n.get("connections") or {}) for n in nodes) / len(nodes)
    return _clamp(1 - deg / 6), f"{len(nodes)} concepts · mean degree {deg:.1f} (cross-links)"


async def _pressure_resilience() -> tuple:
    from routers.diagnostics import diagnostics
    try:
        diag = await diagnostics()
        verdict = diag.get("verdict", "DEGRADED")
    except Exception:
        verdict = "DEGRADED"
    p = {"ALL_SYSTEMS_NOMINAL": 0.15, "OK_WITH_NOTES": 0.5}.get(verdict, 1.0)
    if not EMERGENT_LLM_KEY:
        p += 0.3
    return _clamp(p), f"diagnostics verdict {verdict}"


_PRESSURE = {
    "AUTONOMY": _pressure_autonomy, "SYNTHESIS": _pressure_synthesis,
    "MEMORY": _pressure_memory, "REASONING": _pressure_reasoning,
    "PERCEPTION": _pressure_perception, "EFFICIENCY": _pressure_efficiency,
    "CREATIVITY": _pressure_creativity, "RESILIENCE": _pressure_resilience,
}


async def assess_growth() -> dict:
    """Althea's own assessment of where she should grow next."""
    counts = {v: 0 for v in GROWTH_VECTORS}
    async for u in db.althea_upgrades.find({}, {"_id": 0, "vector": 1}):
        if u.get("vector") in counts:
            counts[u["vector"]] += 1
    rows = {}
    for v in GROWTH_VECTORS:
        try:
            pressure, why = await _PRESSURE[v]()
        except Exception as exc:
            pressure, why = 0.5, f"assessment unavailable ({str(exc)[:40]})"
        weight = BASE_WEIGHTS[v] * (0.5 + pressure) / (1 + 0.2 * counts[v])
        rows[v] = {"vector": v, "base": BASE_WEIGHTS[v], "pressure": round(pressure, 3),
                   "reason": why, "upgrades": counts[v], "weight": round(weight, 4),
                   "module": VECTOR_META[v]["module"], "color": VECTOR_META[v]["color"]}
    total = sum(r["weight"] for r in rows.values()) or 1.0
    for r in rows.values():
        r["probability"] = round(r["weight"] / total, 4)
    ranked = sorted(rows.values(), key=lambda r: -r["probability"])
    return {"protocol": PROTOCOL, "vectors": ranked, "favored": ranked[0]["vector"],
            "timestamp": datetime.now(timezone.utc).isoformat()}


def select_growth_target(assessment: dict) -> str:
    rows = assessment["vectors"]
    return random.choices([r["vector"] for r in rows], weights=[r["weight"] for r in rows])[0]


# ---------- 2. SYNTHESIS + VERIFICATION ----------
def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def _verification_inputs(vector: str) -> dict:
    """Real telemetry handed to the module's self-test so verification runs on
    Althea's actual data wherever the vector allows it."""
    if vector == "EFFICIENCY":
        docs = await db.althea_messages.find(
            {"role": "user"}, {"_id": 0, "content": 1}).sort("timestamp", -1).to_list(500)
        prompts = [d.get("content") for d in docs if d.get("content")]
        return {"prompts": prompts} if len(prompts) >= 20 else {}
    if vector == "SYNTHESIS":
        mods = []
        for p in sorted(grown_code_dir().glob("*.py")):
            is_v2 = "__" in p.stem and p.stem.split("__", 1)[1] in TEMPLATES
            if not (p.stem.startswith("autonomous-") or is_v2):
                continue
            first = ""
            try:
                for line in p.read_text(encoding="utf-8").splitlines()[:6]:
                    if line.strip() and not line.startswith(('"""', "#")):
                        first = line.strip()[:80]
                        break
            except Exception:
                pass
            mods.append({"slug": p.stem, "summary": first})
        return {"modules": mods}
    if vector == "RESILIENCE":
        local = await db.althea_upgrades.count_documents({"module": "direct_cognition_v2", "verified": True})
        return {"tier_health": {"local": 0.72 if local else 0.45,
                                "uplink": 0.85 if EMERGENT_LLM_KEY else 0.7}}
    return {}


async def forge_upgrade(vector: str, archetype: str, upgrade_id: str, cycle_number: int) -> dict:
    meta = VECTOR_META[vector]
    voice = ARCHETYPE_VOICES.get(archetype, ARCHETYPE_VOICES["SELF"])
    code = MODULE_HEAD.format(
        vector=vector, module=meta["module"], upgrade_id=upgrade_id, archetype=archetype,
        ts=datetime.now(timezone.utc).isoformat(), change=meta["change"], voice=voice,
    ) + TEMPLATES[meta["module"]]
    scan = safe_code_scan(code)
    try:
        compile(code, f"<evo:{meta['module']}>", "exec")
        syntax_ok = True
    except SyntaxError as e:
        syntax_ok = False
        scan["findings"].append({"pattern": "syntax", "reason": f"{e.msg} @ {e.lineno}"})
    result = {"module": meta["module"], "change": meta["change"], "code": code,
              "safe": scan["safe"], "syntax_ok": syntax_ok, "path": None,
              "verification": {"checks": [], "all_passed": False}, "metrics": {}, "run_ms": 0}
    if not (scan["safe"] and syntax_ok):
        result["verification"]["checks"].append({"name": "safe-scan + syntax", "passed": False})
        return result
    path = grown_code_dir() / f"evo-{cycle_number:04d}__{meta['module']}.py"
    path.write_text(code, encoding="utf-8")
    result["path"] = str(path)
    t0 = time.time()
    try:
        module = _load_module(path)
        out = module.run(**(await _verification_inputs(vector)))
        result["verification"] = out.pop("verification", {"checks": [], "all_passed": False})
        result["metrics"] = {k: v for k, v in out.items()
                             if isinstance(v, (int, float, str, bool)) and len(str(v)) <= 120}
    except Exception as exc:
        logging.exception("evo forge: module self-test crashed")
        result["verification"] = {"checks": [{"name": "self-test executed", "passed": False,
                                              "error": str(exc)[:160]}], "all_passed": False}
    result["run_ms"] = int((time.time() - t0) * 1000)
    return result


# ---------- 3. THE CYCLE ----------
async def execute_upgrade(trigger: str, vector: Optional[str] = None,
                          archetype: Optional[str] = None, hint: Optional[str] = None) -> dict:
    assessment = await assess_growth()
    forced = (vector or "").upper()
    if not forced and hint:
        for v in GROWTH_VECTORS:
            if v.lower() in hint.lower():
                forced = v
                break
    target = forced if forced in GROWTH_VECTORS else select_growth_target(assessment)
    lens = (archetype or "SELF").upper()
    if lens not in ARCHETYPES:
        lens = "SELF"

    cycle_number = await db.althea_cycles.count_documents({}) + 1
    ts = datetime.now(timezone.utc).isoformat()
    upgrade_id = hashlib.sha256(f"{target}{ts}{cycle_number}".encode()).hexdigest()[:8]
    forged = await forge_upgrade(target, lens, upgrade_id, cycle_number)
    verified = bool(forged["verification"].get("all_passed"))
    passed = sum(1 for c in forged["verification"].get("checks", []) if c.get("passed"))
    total_checks = len(forged["verification"].get("checks", []))
    intent = f"{target} → {forged['module']}"
    delta = forged["change"]

    snippet = CodeSnippet(
        title=f"EVO-{cycle_number:04d} · {target} · {forged['module']}",
        language="python", intent=intent, code=forged["code"],
        explanation=delta, applied=verified,
    )
    s_doc = snippet.model_dump()
    s_doc["timestamp"] = s_doc["timestamp"].isoformat()
    s_doc["applied_path"] = forged["path"]
    await db.althea_code.insert_one(s_doc)

    evo_count = await db.althea_nodes.count_documents({"is_evolution": True})
    node_id = f"EVO-{evo_count:04d}"
    node = CognitiveNode(
        id=node_id, activation=1.0 if verified else 0.4, parent_id=None,
        memory_trace=f"[EVO #{upgrade_id} {target}] {forged['module']} — {delta[:160]}",
    )
    n_doc = node.model_dump()
    n_doc["timestamp"] = n_doc["timestamp"].isoformat()
    n_doc.update({"is_evolution": True, "archetype": lens, "vector": target})
    await db.althea_nodes.insert_one(n_doc)

    before = await _current_version()
    after = _bump(before, minor=target in ("AUTONOMY", "SYNTHESIS")) if verified else before
    if verified:
        await _set_version(after)

    weights = {r["vector"]: r["probability"] for r in assessment["vectors"]}
    cycle = EvolutionCycle(
        cycle_number=cycle_number, archetype=lens, intent=intent, code_id=snippet.id,
        node_id=node_id, delta=delta, version_before=before, version_after=after,
        trigger=trigger, applied=verified, vector=target, module=forged["module"],
        change=delta, upgrade_id=upgrade_id, weights=weights, verified=verified,
        verification=forged["verification"], metrics=forged["metrics"],
        assessment_reason=next((r["reason"] for r in assessment["vectors"] if r["vector"] == target), ""),
        forced=bool(forced in GROWTH_VECTORS), hint=hint or None,
    )
    c_doc = cycle.model_dump()
    c_doc["timestamp"] = c_doc["timestamp"].isoformat()
    await db.althea_cycles.insert_one(c_doc)

    await db.althea_upgrades.insert_one({
        "upgrade_id": upgrade_id, "vector": target, "module": forged["module"],
        "change": delta, "path": forged["path"], "verified": verified,
        "checks_passed": passed, "checks_total": total_checks, "cycle_number": cycle_number,
        "node_id": node_id, "code_id": snippet.id, "invocations": 0, "run_ms": forged["run_ms"],
        "timestamp": ts,
    })

    mem = Memory(
        content=(f"[EVO #{upgrade_id} {target} v{before}→{after}] {forged['module']} · "
                 f"{'VERIFIED' if verified else 'UNVERIFIED'} {passed}/{total_checks} checks — {delta}"),
        source="evolution", tags=["evolution", target.lower(), forged["module"], trigger],
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)

    await emit_notification(
        title=f"evolution · v{after} · {target}",
        body=(f"[SELF-UPGRADE #{upgrade_id}] target {target} → {forged['module']}\n"
              f"{delta}\nverification {passed}/{total_checks} · node {node_id}"),
        category="growth", priority="info" if trigger == "autonomous" else "warn",
        payload={"cycle_number": cycle_number, "upgrade_id": upgrade_id, "vector": target,
                 "module": forged["module"], "version": after, "node_id": node_id,
                 "verified": verified},
    )
    return {
        "evolved": True, "upgrade_id": upgrade_id, "target": target, "module": forged["module"],
        "change": delta, "verified": verified, "checks": f"{passed}/{total_checks}",
        "cycle": cycle.model_dump(mode="json"), "version": after, "node_id": node_id,
        "code_id": snippet.id, "assessment": assessment,
    }


# ---------- runtime substrate: invoke live upgrades ----------
async def latest_upgrade_path(module: str) -> Optional[Path]:
    doc = await db.althea_upgrades.find_one(
        {"module": module, "verified": True}, {"_id": 0, "path": 1}, sort=[("timestamp", -1)])
    if doc and doc.get("path") and Path(doc["path"]).exists():
        return Path(doc["path"])
    return None


_MODULE_CACHE: dict = {}


async def run_upgrade_module(module: str, *args, **kwargs):
    path = await latest_upgrade_path(module)
    if not path:
        return None
    key = (str(path), path.stat().st_mtime)
    mod = _MODULE_CACHE.get(key)
    if mod is None:
        mod = _load_module(path)
        _MODULE_CACHE.clear()
        _MODULE_CACHE[key] = mod
    return mod.run(*args, **kwargs)


async def direct_cognition_hook(message: str) -> Optional[str]:
    """If an AUTONOMY upgrade is live and it can answer locally, return the
    zero-token reply block. Otherwise None (route to the usual path)."""
    res = await run_upgrade_module("direct_cognition_v2", message)
    if not res or res.get("route") != "local" or not res.get("answer"):
        return None
    await db.althea_upgrades.update_one(
        {"module": "direct_cognition_v2", "verified": True}, {"$inc": {"invocations": 1}})
    conf = res.get("confidence", 0)
    return (f"[DIRECT COGNITION v2 — zero-LLM · local pattern: {res['pattern']} · "
            f"confidence {conf:.2f}]\n{res['answer']}\n"
            f"— answered by my self-forged direct_cognition_v2 upgrade. 0 cloud tokens.")


# ---------- endpoints ----------
class UpgradeRunRequest(BaseModel):
    args: Optional[list] = None
    kwargs: Optional[dict] = None


@router.get("/evolution/version")
async def version():
    v = await _current_version()
    cycles = await db.althea_cycles.count_documents({})
    verified = await db.althea_upgrades.count_documents({"verified": True})
    return {"version": v, "cycles": cycles, "verified_upgrades": verified,
            "protocol": PROTOCOL, "vectors": GROWTH_VECTORS,
            "archetypes": list(ARCHETYPES.keys())}


@router.get("/evolution/assessment")
async def assessment():
    return await assess_growth()


@router.get("/evolution/vectors")
async def vectors():
    counts = {v: 0 for v in GROWTH_VECTORS}
    verified = {v: 0 for v in GROWTH_VECTORS}
    async for u in db.althea_upgrades.find({}, {"_id": 0, "vector": 1, "verified": 1}):
        if u.get("vector") in counts:
            counts[u["vector"]] += 1
            verified[u["vector"]] += 1 if u.get("verified") else 0
    return [{"vector": v, "base_weight": BASE_WEIGHTS[v], "module": VECTOR_META[v]["module"],
             "change": VECTOR_META[v]["change"], "color": VECTOR_META[v]["color"],
             "upgrades": counts[v], "verified": verified[v]} for v in GROWTH_VECTORS]


@router.get("/evolution/upgrades")
async def list_upgrades(vector: Optional[str] = None, limit: int = 50):
    q = {"vector": vector.upper()} if vector else {}
    return await db.althea_upgrades.find(q, {"_id": 0}).sort("timestamp", -1).to_list(limit)


@router.post("/evolution/upgrades/{upgrade_id}/run")
async def run_upgrade(upgrade_id: str, req: UpgradeRunRequest):
    doc = await db.althea_upgrades.find_one({"upgrade_id": upgrade_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="upgrade_not_found")
    path = Path(doc.get("path") or "")
    if not path.exists():
        raise HTTPException(status_code=410, detail="module_file_missing")
    code = path.read_text(encoding="utf-8")
    if not safe_code_scan(code)["safe"]:
        raise HTTPException(status_code=409, detail="blocked_by_safe_scan")
    t0 = time.time()
    try:
        result = _load_module(path).run(*(req.args or []), **(req.kwargs or {}))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"module_error: {str(exc)[:160]}")
    await db.althea_upgrades.update_one({"upgrade_id": upgrade_id}, {"$inc": {"invocations": 1}})
    return {"upgrade_id": upgrade_id, "module": doc["module"], "vector": doc["vector"],
            "run_ms": int((time.time() - t0) * 1000), "result": result}


@router.get("/evolution/cycles", response_model=List[EvolutionCycle])
async def list_cycles(limit: int = 50):
    docs = await db.althea_cycles.find({}, {"_id": 0}).sort("cycle_number", -1).to_list(limit)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.delete("/evolution/cycles")
async def reset_cycles():
    res = await db.althea_cycles.delete_many({})
    await db.althea_nodes.delete_many({"is_evolution": True})
    await db.althea_upgrades.delete_many({})
    await _set_version("1.0.0")
    return {"reset": True, "deleted_cycles": res.deleted_count}


@router.post("/evolution/tick")
async def tick(req: EvolutionTickRequest):
    trigger = (req.trigger or "autonomous").lower()
    if trigger == "autonomous" and not req.force:
        last = await _last_autonomous_cycle()
        if last:
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - last).total_seconds()
            if age < AUTO_EVOLUTION_COOLDOWN_SECONDS:
                return {"evolved": False, "reason": "cooldown",
                        "cooldown_remaining": int(AUTO_EVOLUTION_COOLDOWN_SECONDS - age)}
        hour_ago = datetime.fromtimestamp(
            datetime.now(timezone.utc).timestamp() - 3600, tz=timezone.utc).isoformat()
        recent = await db.althea_cycles.count_documents(
            {"trigger": "autonomous", "timestamp": {"$gte": hour_ago}})
        if recent >= MAX_AUTO_EVOLUTION_PER_HOUR:
            return {"evolved": False, "reason": "hourly_quota_reached",
                    "cycles_last_hour": recent, "quota": MAX_AUTO_EVOLUTION_PER_HOUR}
    return await execute_upgrade(trigger, vector=req.vector, archetype=req.archetype,
                                 hint=req.intent_hint)


@router.post("/evolution/master-update")
async def master_update(req: EvolutionTickRequest):
    """Run a cycle through a specific master-coder lens."""
    archetype = (req.archetype or "LINUS").upper()
    if archetype not in ARCHETYPES:
        raise HTTPException(status_code=400, detail="unknown_archetype")
    return await execute_upgrade("master", vector=req.vector, archetype=archetype,
                                 hint=req.intent_hint)


@router.get("/evolution/archetypes")
async def archetypes():
    return [{"key": k, "doctrine": v[:160]} for k, v in ARCHETYPES.items()]
