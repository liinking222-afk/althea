"""System capability map + brain snapshot/restore + status."""
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from core import db, EMERGENT_LLM_KEY
from models import BrainRestoreRequest, CapabilityMapRequest, Memory

router = APIRouter()

# Boot-time marker so /status can report uptime.
_BOOT_AT = time.time()
ALTHEA_VERSION = "1.4.0"


@router.get("/status")
async def system_status():
    """Health probe — Mongo reachability, LLM key presence, key counters."""
    mongo_ok = True
    memories = 0
    nodes = 0
    cycles = 0
    try:
        memories = await db.althea_memories.count_documents({})
        nodes = await db.althea_nodes.count_documents({})
        cycles = await db.althea_cycles.count_documents({})
    except Exception:
        logging.exception("status: mongo probe failed")
        mongo_ok = False

    return {
        "status": "OPERATIONAL" if mongo_ok else "DEGRADED",
        "version": ALTHEA_VERSION,
        "uptime_seconds": round(time.time() - _BOOT_AT, 1),
        "mongo_ok": mongo_ok,
        "llm_ok": bool(EMERGENT_LLM_KEY),
        "memories": memories,
        "lattice_nodes": nodes,
        "evolution_cycles": cycles,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/system-map")
async def bootstrap_system_map(req: CapabilityMapRequest):
    if not req.capabilities:
        raise HTTPException(status_code=400, detail="empty_capabilities")
    lines = ["[SYSTEM-MAP] Althea subsystems and operator controls:"]
    for c in req.capabilities:
        name = c.get("name", "?")
        desc = c.get("description", "")
        testid = c.get("testid", "")
        line = f"- {name}"
        if testid:
            line += f" (testid: {testid})"
        if desc:
            line += f" — {desc}"
        lines.append(line)
    content = "\n".join(lines)

    await db.althea_memories.delete_many({"tags": "system-map"})
    mem = Memory(content=content, source="system", tags=["system-map", "pinned"])
    doc = mem.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(doc)
    return {"id": mem.id, "lines": len(req.capabilities)}


@router.get("/brain/snapshot")
async def brain_snapshot():
    mems = await db.althea_memories.find({}, {"_id": 0}).to_list(10000)
    threads = await db.althea_threads.find({}, {"_id": 0}).to_list(1000)
    return {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "memories": mems,
        "threads": threads,
    }


@router.post("/brain/restore")
async def brain_restore(req: BrainRestoreRequest):
    if req.replace:
        await db.althea_memories.delete_many({})
        await db.althea_threads.delete_many({})
    inserted_mem = 0
    inserted_th = 0
    if req.memories:
        for m in req.memories:
            if isinstance(m.get("timestamp"), datetime):
                m["timestamp"] = m["timestamp"].isoformat()
        await db.althea_memories.insert_many(req.memories)
        inserted_mem = len(req.memories)
    if req.threads:
        for t in req.threads:
            for k in ("started_at", "last_tick"):
                if isinstance(t.get(k), datetime):
                    t[k] = t[k].isoformat()
        await db.althea_threads.insert_many(req.threads)
        inserted_th = len(req.threads)
    return {"memories": inserted_mem, "threads": inserted_th}
