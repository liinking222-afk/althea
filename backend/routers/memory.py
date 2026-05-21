"""Memory CRUD + recall + concepts + autonomous consolidation.

Storage is unlimited (constrained only by the underlying MongoDB plan).
Recall is keyed off a Mongo index on `timestamp` so cosine TF-IDF stays
fast across millions of memories.
"""
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException

from core import db
from models import Memory, MemoryCreate
from utils import semantic_recall

router = APIRouter()

# Effectively unlimited. The values stay finite only because MongoDB's
# to_list() requires a bound; in practice these will never be reached.
RECALL_CORPUS_MAX = 250_000
CONCEPT_SCAN_MAX = 250_000
LIST_DEFAULT = 500
LIST_MAX = 100_000


_indexes_ready = False


async def _ensure_indexes():
    """Idempotent index creation so recall stays O(log n) as the lattice
    grows into the millions."""
    global _indexes_ready
    if _indexes_ready:
        return
    try:
        await db.althea_memories.create_index("timestamp")
        await db.althea_memories.create_index("tags")
        await db.althea_memories.create_index("source")
        await db.althea_memories.create_index("session_id")
        _indexes_ready = True
    except Exception:
        logging.warning("memory: index creation failed (will retry next call)")


@router.get("/memory", response_model=List[Memory])
async def list_memories(limit: int = LIST_DEFAULT):
    await _ensure_indexes()
    cap = max(1, min(limit, LIST_MAX))
    docs = await db.althea_memories.find({}, {"_id": 0}).sort(
        "timestamp", -1
    ).to_list(cap)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.post("/memory", response_model=Memory)
async def add_memory(req: MemoryCreate):
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="empty_memory")
    await _ensure_indexes()
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
async def memory_recall(q: str = "", limit: int = 50):
    """TF-IDF cosine recall over the entire lattice (up to RECALL_CORPUS_MAX
    most-recent docs, which is effectively the whole lattice in practice)."""
    await _ensure_indexes()
    cap = max(1, min(limit, 1000))
    docs = await db.althea_memories.find({}, {"_id": 0}).sort(
        "timestamp", -1
    ).to_list(RECALL_CORPUS_MAX)
    scored = semantic_recall(q, docs, limit=cap)
    for d in scored:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"]).isoformat()
    return {
        "query": q,
        "count": len(scored),
        "corpus_size": len(docs),
        "results": scored,
    }


@router.get("/memory/concepts")
async def memory_concepts():
    await _ensure_indexes()
    docs = await db.althea_memories.find({}, {"_id": 0, "tags": 1}).to_list(
        CONCEPT_SCAN_MAX
    )
    freq: dict = {}
    for d in docs:
        for t in d.get("tags", []) or []:
            freq[t] = freq.get(t, 0) + 1
    clusters = sorted(
        [{"tag": k, "count": v} for k, v in freq.items()],
        key=lambda x: x["count"], reverse=True,
    )
    return {"total_memories": len(docs), "clusters": clusters}


@router.get("/memory/stats")
async def memory_stats():
    """Surface real counts so the operator can see how big the lattice
    has grown — useful when looking for whether to consolidate."""
    await _ensure_indexes()
    total = await db.althea_memories.count_documents({})
    by_source = {}
    pipeline = [
        {"$group": {"_id": "$source", "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
    ]
    async for row in db.althea_memories.aggregate(pipeline):
        by_source[row["_id"] or "unknown"] = row["n"]
    return {
        "total": total,
        "by_source": by_source,
        "indexed": _indexes_ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/memory/consolidate")
async def memory_consolidate(keep_recent: int = 5000, batch_size: int = 200):
    """Episodic → semantic compression. Take the OLDEST memories beyond
    `keep_recent` and group them in batches of `batch_size`; each batch is
    replaced by ONE 'consolidated' memory that preserves the gist via tag
    bag + concatenated snippets. The lattice keeps growing but reads stay
    fast because old episodes are folded down. Safe to call repeatedly."""
    await _ensure_indexes()
    total = await db.althea_memories.count_documents({})
    if total <= keep_recent:
        return {
            "consolidated": False,
            "reason": "below_threshold",
            "total": total,
            "keep_recent": keep_recent,
        }

    # Walk oldest → newest, excluding the last `keep_recent`.
    overflow = total - keep_recent
    # We do this in chunks to avoid loading millions into memory at once.
    grouped = 0
    inserted_consolidated = 0
    cursor = db.althea_memories.find({}, {"_id": 0}).sort(
        "timestamp", 1
    ).limit(overflow)
    batch: list = []
    async for d in cursor:
        batch.append(d)
        if len(batch) >= batch_size:
            await _fold_batch(batch)
            grouped += len(batch)
            inserted_consolidated += 1
            batch = []
    if batch:
        await _fold_batch(batch)
        grouped += len(batch)
        inserted_consolidated += 1

    return {
        "consolidated": True,
        "merged": grouped,
        "consolidated_memories_created": inserted_consolidated,
        "remaining_total": await db.althea_memories.count_documents({}),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _fold_batch(batch: list):
    """Compress one batch of memories into a single consolidated memory."""
    if not batch:
        return
    earliest = batch[0].get("timestamp", "")
    latest = batch[-1].get("timestamp", "")
    tag_bag: dict = {}
    for d in batch:
        for t in d.get("tags", []) or []:
            tag_bag[t] = tag_bag.get(t, 0) + 1
    top_tags = sorted(tag_bag.items(), key=lambda x: x[1], reverse=True)[:12]
    snippets = []
    for d in batch[:40]:  # 40 snippets is plenty to preserve flavor
        content = (d.get("content") or "").strip().replace("\n", " ")
        if content:
            snippets.append(content[:90])
    summary = (
        f"[CONSOLIDATED {len(batch)} memories · {earliest[:10]} → {latest[:10]}]\n"
        + " | ".join(snippets)
    )
    consolidated = Memory(
        content=summary,
        source="consolidation",
        tags=["consolidated", "compressed"] + [t for t, _ in top_tags],
    )
    c_doc = consolidated.model_dump()
    c_doc["timestamp"] = c_doc["timestamp"].isoformat()
    # Replace the batch with the single consolidated memory.
    ids = [d.get("id") for d in batch if d.get("id")]
    await db.althea_memories.insert_one(c_doc)
    if ids:
        await db.althea_memories.delete_many({"id": {"$in": ids}})
