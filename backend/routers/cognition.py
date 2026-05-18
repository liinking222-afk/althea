"""Autonomous cognition threads."""
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException

from core import db, EMERGENT_LLM_KEY
from models import (
    CognitionThread,
    Memory,
    ThreadCreate,
    TickResponse,
)

from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()

# Minimum seconds between Claude calls per thread.
TICK_THROTTLE_SECONDS = 25


def _coerce_thread_dates(d: dict) -> dict:
    for k in ("started_at", "last_tick"):
        v = d.get(k)
        if isinstance(v, str):
            d[k] = datetime.fromisoformat(v)
    return d


@router.post("/cognition/threads", response_model=CognitionThread)
async def create_thread(req: ThreadCreate):
    if not req.focus_query.strip():
        raise HTTPException(status_code=400, detail="empty_focus")
    th = CognitionThread(focus_query=req.focus_query.strip())
    doc = th.model_dump()
    doc["started_at"] = doc["started_at"].isoformat()
    if doc.get("last_tick"):
        doc["last_tick"] = doc["last_tick"].isoformat()
    await db.althea_threads.insert_one(doc)
    return th


@router.get("/cognition/threads", response_model=List[CognitionThread])
async def list_threads(active_only: bool = True):
    q = {"active": True} if active_only else {}
    docs = await db.althea_threads.find(q, {"_id": 0}).sort(
        "started_at", -1
    ).to_list(200)
    for d in docs:
        _coerce_thread_dates(d)
    return docs


@router.delete("/cognition/threads/{thread_id}")
async def stop_thread(thread_id: str):
    res = await db.althea_threads.update_one(
        {"id": thread_id}, {"$set": {"active": False}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"stopped": thread_id}


@router.post("/cognition/threads/{thread_id}/tick", response_model=TickResponse)
async def tick_thread(thread_id: str):
    doc = await db.althea_threads.find_one({"id": thread_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="not_found")
    if not doc.get("active", True):
        raise HTTPException(status_code=410, detail="thread_inactive")

    # Throttle: if last_tick is < TICK_THROTTLE_SECONDS old, return cached insight
    # without firing another Claude call.
    last_tick_raw = doc.get("last_tick")
    if last_tick_raw:
        last_tick_dt = (
            datetime.fromisoformat(last_tick_raw)
            if isinstance(last_tick_raw, str)
            else last_tick_raw
        )
        if last_tick_dt.tzinfo is None:
            last_tick_dt = last_tick_dt.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - last_tick_dt).total_seconds()
        if age < TICK_THROTTLE_SECONDS and doc.get("last_insight"):
            return TickResponse(
                thread_id=thread_id,
                iterations=doc.get("iterations", 0),
                insight=doc["last_insight"],
                novelty=doc.get("last_novelty", 0.0),
                cached=True,
                timestamp=last_tick_dt.isoformat(),
            )

    # Recent memories for context
    mem_docs = await db.althea_memories.find(
        {}, {"_id": 0, "content": 1, "tags": 1}
    ).sort("timestamp", -1).to_list(15)
    mem_lines = "\n".join(f"- {m.get('content','')[:200]}" for m in mem_docs)

    insight = "(no insight this cycle)"
    novelty = 0.0
    if EMERGENT_LLM_KEY:
        try:
            sys_prompt = (
                "You are ALTHEA running a background cognition thread. "
                "You are NOT replying to the operator. You are silently iterating on a focus query. "
                "Produce ONE concise insight (1-2 sentences) and a novelty score 0.0-1.0 estimating how new this is relative to your memories. "
                "Reply EXACTLY in two lines:\n"
                "INSIGHT: <one-or-two sentence insight>\n"
                "NOVELTY: <0.0-1.0>"
            )
            user_text = (
                f"FOCUS: {doc['focus_query']}\n"
                f"ITERATION: {doc.get('iterations', 0) + 1}\n"
                f"RECENT MEMORY:\n{mem_lines or '(empty)'}"
            )
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"thread-{thread_id}-{doc.get('iterations', 0)}",
                system_message=sys_prompt,
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")
            raw = await chat.send_message(UserMessage(text=user_text))
            for line in raw.splitlines():
                if line.strip().upper().startswith("INSIGHT:"):
                    insight = line.split(":", 1)[1].strip()
                elif line.strip().upper().startswith("NOVELTY:"):
                    try:
                        novelty = float(line.split(":", 1)[1].strip())
                    except ValueError:
                        novelty = 0.0
            novelty = max(0.0, min(1.0, novelty))
        except Exception:
            logging.exception("tick failure")
            insight = "[CORE-LATENCY] background thread stalled this cycle."

    now = datetime.now(timezone.utc)
    iterations = doc.get("iterations", 0) + 1
    await db.althea_threads.update_one(
        {"id": thread_id},
        {"$set": {
            "iterations": iterations,
            "last_insight": insight,
            "last_novelty": novelty,
            "last_tick": now.isoformat(),
        }},
    )

    if novelty >= 0.7:
        mem = Memory(
            content=f"[INSIGHT thread:{thread_id[:8]} focus:'{doc['focus_query'][:60]}'] {insight}",
            source="thread",
            tags=["insight", f"thread:{thread_id[:8]}"],
        )
        m_doc = mem.model_dump()
        m_doc["timestamp"] = m_doc["timestamp"].isoformat()
        await db.althea_memories.insert_one(m_doc)

    return TickResponse(
        thread_id=thread_id,
        iterations=iterations,
        insight=insight,
        novelty=novelty,
        cached=False,
        timestamp=now.isoformat(),
    )
