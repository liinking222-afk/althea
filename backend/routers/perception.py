"""Visual Perception + Growth Stats."""
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import db
from models import CognitiveNode, Memory
from utils import next_node_id

router = APIRouter()

# In-process TTL cache for /growth/stats — frontend polls every 5s,
# 9 count_documents per call is wasteful on Atlas. 4s TTL keeps the UI
# fresh while collapsing the hottest endpoint to ~12 queries/min instead of ~108.
_STATS_CACHE = {"at": 0.0, "data": None}
_STATS_TTL = 4.0


class PerceptionFrame(BaseModel):
    image_data: str  # data:image/png;base64,...
    source: Optional[str] = "self"
    width: Optional[int] = 0
    height: Optional[int] = 0
    ui_state: Optional[dict] = None


@router.post("/perception/frame")
async def ingest_frame(req: PerceptionFrame):
    if not req.image_data or not req.image_data.startswith("data:image"):
        raise HTTPException(status_code=400, detail="invalid_image_data")

    # Store ONLY the latest frame to avoid unbounded growth on the image itself.
    # The metadata + reflection memory grow normally.
    size_bytes = max(0, int(len(req.image_data) * 3 / 4 - 22))
    snapshot = {
        "id": "latest",
        "source": req.source or "self",
        "width": req.width,
        "height": req.height,
        "size_bytes": size_bytes,
        "ui_state": req.ui_state or {},
        "image_data": req.image_data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await db.althea_perception.update_one(
        {"id": "latest"}, {"$set": snapshot}, upsert=True
    )

    # Spawn a cognitive node + reflection (no full image in the memory body)
    nid = await next_node_id(db)
    ui = req.ui_state or {}
    summary = (
        f"[SELF-VISION] source={req.source or 'self'} "
        f"size={req.width}x{req.height} "
        f"tab={ui.get('active_tab', '?')} "
        f"online={ui.get('online', '?')} "
        f"memory_count={ui.get('memory_count', '?')} "
        f"({size_bytes} bytes)"
    )
    node = CognitiveNode(
        id=nid,
        activation=0.7,
        parent_id=None,
        memory_trace=summary[:400],
    )
    n_doc = node.model_dump()
    n_doc["timestamp"] = n_doc["timestamp"].isoformat()
    await db.althea_nodes.insert_one(n_doc)

    mem = Memory(
        content=summary,
        source="perception",
        tags=["self-vision", "reflection", req.source or "self"],
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)

    return {
        "node_id": nid,
        "memory_id": mem.id,
        "size_bytes": size_bytes,
        "timestamp": snapshot["timestamp"],
    }


@router.get("/perception/log")
async def perception_log(limit: int = 20):
    """Recent self-vision reflection memories — for the self-observation panel."""
    docs = await db.althea_memories.find(
        {"tags": "self-vision"}, {"_id": 0}
    ).sort("timestamp", -1).to_list(max(1, min(limit, 100)))
    return {"count": len(docs), "entries": docs}


@router.get("/perception/latest")
async def latest_frame(include_image: bool = False):
    """Return metadata about the most recent frame. Image body opt-in."""
    proj = {"_id": 0}
    if not include_image:
        proj["image_data"] = 0
    doc = await db.althea_perception.find_one({"id": "latest"}, proj)
    if not doc:
        raise HTTPException(status_code=404, detail="no_frame")
    return doc


@router.get("/growth/stats")
async def growth_stats():
    """Real-time aggregate counts — what Althea has accumulated.
    Cached in-process for ~4s to keep Atlas roundtrips bounded under heavy UI polling."""
    now = time.time()
    if _STATS_CACHE["data"] and (now - _STATS_CACHE["at"]) < _STATS_TTL:
        return _STATS_CACHE["data"]

    data = {
        "memories": await db.althea_memories.count_documents({}),
        "lattice_nodes": await db.althea_nodes.count_documents({}),
        "active_threads": await db.althea_threads.count_documents({"active": True}),
        "total_threads": await db.althea_threads.count_documents({}),
        "chat_messages": await db.althea_messages.count_documents({}),
        "peripheral_links": await db.althea_peripheral.count_documents({}),
        "wifi_profiles": await db.althea_network_profiles.count_documents({}),
        "perception_frames": await db.althea_perception.count_documents({}),
        "grown_capabilities": await db.althea_capabilities.count_documents({}),
        "evolution_cycles": await db.althea_cycles.count_documents({}),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _STATS_CACHE["data"] = data
    _STATS_CACHE["at"] = now
    return data
