"""Memory CRUD + recall + concepts."""
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from core import db
from models import Memory, MemoryCreate
from utils import semantic_recall

router = APIRouter()


@router.get("/memory", response_model=List[Memory])
async def list_memories(limit: int = 200):
    docs = await db.althea_memories.find({}, {"_id": 0}).sort(
        "timestamp", -1
    ).to_list(limit)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.post("/memory", response_model=Memory)
async def add_memory(req: MemoryCreate):
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="empty_memory")
    mem = Memory(
        content=req.content.strip(),
        source=req.source or "manual",
        session_id=req.session_id,
        tags=req.tags or [],
    )
    doc = mem.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(doc)
    return mem


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str):
    result = await db.althea_memories.delete_one({"id": memory_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"deleted": result.deleted_count}


@router.delete("/memory")
async def clear_memories():
    result = await db.althea_memories.delete_many({})
    return {"deleted": result.deleted_count}


@router.get("/memory/recall")
async def memory_recall(q: str = "", limit: int = 25):
    """TF-IDF cosine recall over all memories."""
    docs = await db.althea_memories.find({}, {"_id": 0}).sort(
        "timestamp", -1
    ).to_list(2000)
    scored = semantic_recall(q, docs, limit=limit)
    for d in scored:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"]).isoformat()
    return {"query": q, "count": len(scored), "results": scored}


@router.get("/memory/concepts")
async def memory_concepts():
    docs = await db.althea_memories.find({}, {"_id": 0, "tags": 1}).to_list(5000)
    freq: dict = {}
    for d in docs:
        for t in d.get("tags", []) or []:
            freq[t] = freq.get(t, 0) + 1
    clusters = sorted(
        [{"tag": k, "count": v} for k, v in freq.items()],
        key=lambda x: x["count"], reverse=True,
    )
    return {"total_memories": len(docs), "clusters": clusters}
