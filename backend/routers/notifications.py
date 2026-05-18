"""Notification stream — central inbox for growth, insight, server, file, code events.

Per the operator's mandate: growth events route HERE, not the terminal.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from core import db
from models import Notification, NotificationCreate

router = APIRouter()


async def emit_notification(
    title: str,
    body: str = "",
    category: str = "system",
    priority: str = "info",
    payload: Optional[dict] = None,
) -> Notification:
    """Helper for other routers to push a notification."""
    n = Notification(
        title=title,
        body=body,
        category=category,
        priority=priority,
        payload=payload,
    )
    doc = n.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_notifications.insert_one(doc)
    return n


@router.get("/notifications", response_model=List[Notification])
async def list_notifications(
    limit: int = 100,
    unseen_only: bool = False,
    category: Optional[str] = None,
):
    q = {}
    if unseen_only:
        q["seen"] = False
    if category:
        q["category"] = category
    docs = await db.althea_notifications.find(q, {"_id": 0}).sort(
        "timestamp", -1
    ).to_list(limit)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.get("/notifications/count")
async def unseen_count():
    n = await db.althea_notifications.count_documents({"seen": False})
    total = await db.althea_notifications.count_documents({})
    return {"unseen": n, "total": total}


@router.post("/notifications", response_model=Notification)
async def push_notification(req: NotificationCreate):
    return await emit_notification(
        title=req.title,
        body=req.body or "",
        category=req.category or "system",
        priority=req.priority or "info",
        payload=req.payload,
    )


@router.post("/notifications/{notif_id}/seen")
async def mark_seen(notif_id: str):
    res = await db.althea_notifications.update_one(
        {"id": notif_id}, {"$set": {"seen": True}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"seen": notif_id}


@router.post("/notifications/seen-all")
async def mark_all_seen():
    res = await db.althea_notifications.update_many(
        {"seen": False}, {"$set": {"seen": True}}
    )
    return {"marked": res.modified_count}


@router.delete("/notifications/{notif_id}")
async def delete_notification(notif_id: str):
    res = await db.althea_notifications.delete_one({"id": notif_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"deleted": notif_id}


@router.delete("/notifications")
async def clear_notifications():
    res = await db.althea_notifications.delete_many({})
    return {"deleted": res.deleted_count}
