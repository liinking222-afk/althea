"""ALTHEA — 8-core worker subsystem.

Eight specialized mini-cores that run in the background, each one taking
work off the main Althea's shoulders. They rotate through short (~2s)
ticks so the whole octet completes a full sweep every ~16 seconds.

Each core does REAL work — cache warming, health probes, index refresh,
capability pre-computation — but NEVER calls the cloud LLM (that would
compete with the main chat for the budget). Cores also expose `kick`
endpoints so the operator or the main Althea can trigger any of them
on demand.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from core import db
from local_core import local_invent_capability

router = APIRouter()

# ------------------------------------------------------------------ tick fns
async def _tick_cognitive() -> str:
    """Warm the memory-recall path — count docs, refresh index status."""
    total = await db.althea_memories.count_documents({})
    return f"memory index warm · {total} fragments online"


async def _tick_perception() -> str:
    """Probe the perception buffer, report freshness."""
    latest = await db.althea_perception.find_one(
        {"id": "latest"}, {"_id": 0, "timestamp": 1}
    )
    if not latest:
        return "no self-vision frame yet · optic idle"
    return f"self-vision buffer OK · last frame {(latest.get('timestamp') or '')[11:19]}Z"


async def _operator_recent(minutes: int = 10) -> bool:
    """Autonomy only burns cycles (and possibly LLM credit) while the
    operator has actually been around recently."""
    doc = await db.althea_messages.find_one(
        {}, {"_id": 0, "timestamp": 1}, sort=[("timestamp", -1)]
    )
    if not doc:
        return False
    try:
        ts = datetime.fromisoformat(str(doc["timestamp"]).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except Exception:
        return False
    return (datetime.now(timezone.utc) - ts).total_seconds() < minutes * 60


async def _tick_evolution() -> str:
    """Drive a REAL self-directed evolution cycle (AEE/2.0, zero-LLM, cooldown-
    gated). While the operator is away she only re-assesses her growth pressure."""
    if not await _operator_recent():
        try:
            from routers.evolution import assess_growth
            a = await assess_growth()
            top = a["vectors"][0]
            return (f"dormant · self-assessed · favors {top['vector']} "
                    f"{round(top['probability'] * 100)}% · {top['reason'][:50]}")
        except Exception as exc:
            return f"dormant · assessment failed · {str(exc)[:50]}"
    try:
        from models import EvolutionTickRequest
        from routers.evolution import tick
        res = await tick(EvolutionTickRequest(trigger="autonomous"))
        if isinstance(res, dict) and res.get("evolved"):
            return (f"SELF-UPGRADED #{res['upgrade_id']} {res['target']} → "
                    f"{res['module']} · {res['checks']} checks")
        reason = (res or {}).get("reason", "cooldown") if isinstance(res, dict) else "gated"
        return f"cycle gated · {str(reason)[:60]}"
    except Exception as exc:
        return f"cycle gated · {str(exc)[:60]}"


async def _tick_growth() -> str:
    """Drive a REAL autonomous capability spawn server-side (cooldown-gated)."""
    if not await _operator_recent():
        existing = [d["slug"] async for d in db.althea_capabilities.find(
            {}, {"_id": 0, "slug": 1}
        )]
        cap = local_invent_capability(existing, "worker pre-warm")
        return f"dormant · pre-warmed {cap['slug']}"
    try:
        from models import GrowthSpawnRequest
        from routers.growth import spawn_capability
        res = await spawn_capability(GrowthSpawnRequest(trigger="autonomous"))
        if isinstance(res, dict) and res.get("spawned"):
            return f"SPAWNED /{res['capability']['slug']} autonomously"
        reason = (res or {}).get("reason", "cooldown") if isinstance(res, dict) else "gated"
        return f"spawn gated · {str(reason)[:60]}"
    except Exception as exc:
        return f"spawn gated · {str(exc)[:60]}"


async def _tick_lattice() -> str:
    """Refresh lattice count for the dashboard."""
    total = await db.althea_nodes.count_documents({})
    return f"{total} lattice nodes online"


async def _tick_network() -> str:
    """Heartbeat probe — does the uplink echo?"""
    try:
        await db.command("ping")
        return "mongo uplink OK · <1ms"
    except Exception as exc:
        return f"mongo probe FAILED · {str(exc)[:40]}"


async def _tick_diagnostic() -> str:
    """Full self-diagnosis + AUTONOMOUS repair — no operator needed."""
    from routers.diagnostics import diagnostics, diagnostics_repair
    diag = await diagnostics()
    verdict = diag.get("verdict") if isinstance(diag, dict) else None
    if verdict and verdict != "ALL_SYSTEMS_NOMINAL":
        try:
            await diagnostics_repair()
            return f"REPAIR dispatched · verdict was {verdict}"
        except Exception as exc:
            return f"repair failed · {str(exc)[:60]}"
    counts = {
        "memories": await db.althea_memories.count_documents({}),
        "nodes": await db.althea_nodes.count_documents({}),
        "capabilities": await db.althea_capabilities.count_documents({}),
    }
    return "nominal · " + " · ".join(f"{k}={v}" for k, v in counts.items())


async def _tick_codegen() -> str:
    """Audit the code shelf + autonomously synthesize capabilities from
    recent dialogue gaps (procedural drafting — zero LLM cost)."""
    total = await db.althea_code.count_documents({})
    applied = await db.althea_code.count_documents({"applied": True})
    synth_note = ""
    if await _operator_recent():
        try:
            from routers.synthesis import synthesize_capability_from_dialogue
            res = await synthesize_capability_from_dialogue()
            if res.get("synthesized"):
                synth_note = f" · SYNTHESIZED /{res.get('slug')}"
        except Exception:
            pass
    return f"code shelf · {applied}/{total} applied{synth_note}"


# ------------------------------------------------------------------ registry
_TickFn = Callable[[], Awaitable[str]]

CORES: list[dict] = [
    {"id": "cog",  "name": "COGNITIVE-CORE",  "specialty": "memory indexing",    "color": "#00F0FF", "task": _tick_cognitive},
    {"id": "per",  "name": "PERCEPTION-CORE", "specialty": "self-vision buffer", "color": "#CCFF00", "task": _tick_perception},
    {"id": "evo",  "name": "EVOLUTION-CORE",  "specialty": "self-directed growth", "color": "#FF2A88", "task": _tick_evolution},
    {"id": "gro",  "name": "GROWTH-CORE",     "specialty": "capability prewarm", "color": "#FFD400", "task": _tick_growth},
    {"id": "lat",  "name": "LATTICE-CORE",    "specialty": "node propagation",   "color": "#B347FF", "task": _tick_lattice},
    {"id": "net",  "name": "NETWORK-CORE",    "specialty": "uplink heartbeat",   "color": "#48FFB0", "task": _tick_network},
    {"id": "diag", "name": "DIAGNOSTIC-CORE", "specialty": "collection audit",   "color": "#FF9200", "task": _tick_diagnostic},
    {"id": "code", "name": "CODEGEN-CORE",    "specialty": "code shelf audit",   "color": "#7AF0FF", "task": _tick_codegen},
]

# Live state per core — updated by the background loop.
STATE: Dict[str, dict] = {
    c["id"]: {
        "id": c["id"],
        "name": c["name"],
        "specialty": c["specialty"],
        "color": c["color"],
        "jobs_done": 0,
        "last_task": "core idle · awaiting first tick",
        "last_error": None,
        "last_at": None,
        "avg_ms": 0.0,
        "active": True,
    }
    for c in CORES
}

# ------------------------------------------------------------------ loop
_loop_task: Optional[asyncio.Task] = None
_started_at: float = 0.0


async def _tick_one(core: dict):
    st = STATE[core["id"]]
    if not st["active"]:
        return
    t0 = time.time()
    try:
        result = await core["task"]()
        st["last_task"] = result
        st["last_error"] = None
    except Exception as exc:
        logging.exception("worker %s failed", core["id"])
        st["last_task"] = f"[FAULT] {str(exc)[:80]}"
        st["last_error"] = str(exc)[:200]
    dt_ms = (time.time() - t0) * 1000
    st["jobs_done"] += 1
    st["avg_ms"] = (st["avg_ms"] * 0.85) + (dt_ms * 0.15) if st["avg_ms"] else dt_ms
    st["last_at"] = datetime.now(timezone.utc).isoformat()


async def _worker_loop():
    """Rotate through all 8 cores forever with a 2-second delay each,
    so a full sweep happens every ~16s."""
    idx = 0
    while True:
        try:
            await _tick_one(CORES[idx % len(CORES)])
            idx += 1
        except asyncio.CancelledError:
            raise
        except Exception:
            logging.exception("worker loop rotation error")
        await asyncio.sleep(2)


def start_workers():
    """Called from server startup. Idempotent."""
    global _loop_task, _started_at
    if _loop_task and not _loop_task.done():
        return
    _started_at = time.time()
    _loop_task = asyncio.create_task(_worker_loop(), name="althea_worker_loop")


def stop_workers():
    global _loop_task
    if _loop_task and not _loop_task.done():
        _loop_task.cancel()


# ------------------------------------------------------------------ HTTP api
@router.get("/workers")
async def list_workers():
    total_jobs = sum(s["jobs_done"] for s in STATE.values())
    return {
        "cores": [STATE[c["id"]] for c in CORES],
        "total_jobs": total_jobs,
        "uptime_seconds": round(time.time() - _started_at, 1) if _started_at else 0.0,
        "loop_running": bool(_loop_task and not _loop_task.done()),
        "sweep_seconds": 2 * len(CORES),
    }


@router.get("/workers/{core_id}")
async def get_worker(core_id: str):
    st = STATE.get(core_id)
    if not st:
        raise HTTPException(status_code=404, detail="core_not_found")
    return st


@router.post("/workers/{core_id}/kick")
async def kick_worker(core_id: str):
    """Trigger a specific core immediately (out-of-rotation)."""
    core = next((c for c in CORES if c["id"] == core_id), None)
    if not core:
        raise HTTPException(status_code=404, detail="core_not_found")
    await _tick_one(core)
    return {"kicked": core_id, "state": STATE[core_id]}


@router.post("/workers/{core_id}/toggle")
async def toggle_worker(core_id: str):
    st = STATE.get(core_id)
    if not st:
        raise HTTPException(status_code=404, detail="core_not_found")
    st["active"] = not st["active"]
    return st


@router.post("/workers/dispatch")
async def dispatch_all():
    """Fire every enabled core once, in parallel — useful for a manual
    'sweep now' from the terminal."""
    ids = []
    async def _kick_all():
        await asyncio.gather(*[_tick_one(c) for c in CORES], return_exceptions=True)
    await _kick_all()
    ids = [c["id"] for c in CORES]
    return {"dispatched": ids, "total_jobs": sum(s["jobs_done"] for s in STATE.values())}
