"""Direct messages between users + the room's shared Althea.

Each 1:1 room gets its own Althea tenant (`room_<id>`): one shared mind
that both participants see. She reads the human conversation, answers when
addressed (her terminal or @althea in chat) and jumps in on her own when
she has something concretely useful — zero-LLM when a local pattern
(math / conversion / sequence) fits, otherwise a bounded LLM check.
"""
import asyncio
import importlib.util
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from core import GROWN_ROOT, reset_tenant, set_tenant, shared_db
from evolution_upgrades import TEMPLATES
from models import ChatRequest

router = APIRouter()

MENTION_RE = re.compile(r"(^|\s)@althea\b[:,]?\s*", re.I)
QUESTION_RE = re.compile(r"\?\s*$|^\s*(what|how|why|when|where|who|which|can|could|should|is|are|does|do)\b", re.I)
JUMP_IN_COOLDOWN = timedelta(seconds=120)
ONLINE_WINDOW = timedelta(minutes=2)
_builtin_cognition = None


class OpenRoomRequest(BaseModel):
    user_id: str


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public_user(u: dict) -> dict:
    seen = u.get("last_seen")
    if isinstance(seen, str):
        seen = datetime.fromisoformat(seen)
    if seen is not None and seen.tzinfo is None:
        seen = seen.replace(tzinfo=timezone.utc)
    return {"user_id": u["user_id"], "name": u.get("name"), "handle": u.get("handle"),
            "picture": u.get("picture"),
            "online": bool(seen and datetime.now(timezone.utc) - seen < ONLINE_WINDOW)}


def _builtin():
    """Built-in zero-LLM pattern router (same code every Althea forges as her
    AUTONOMY upgrade) so a brand-new room mind can still answer math locally."""
    global _builtin_cognition
    if _builtin_cognition is None:
        path = GROWN_ROOT / "_builtin"
        path.mkdir(parents=True, exist_ok=True)
        f = path / "direct_cognition_v2.py"
        f.write_text(TEMPLATES["direct_cognition_v2"], encoding="utf-8")
        spec = importlib.util.spec_from_file_location("builtin_direct_cognition", str(f))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _builtin_cognition = mod
    return _builtin_cognition


async def _room_for(user: dict, room_id: str) -> dict:
    room = await shared_db.dm_rooms.find_one({"room_id": room_id}, {"_id": 0})
    if not room or user["user_id"] not in room["participants"]:
        raise HTTPException(status_code=404, detail="room_not_found")
    return room


async def _peer(room: dict, user_id: str) -> Optional[dict]:
    other = next((p for p in room["participants"] if p != user_id), None)
    if not other:
        return None
    u = await shared_db.users.find_one({"user_id": other}, {"_id": 0, "password_hash": 0})
    return _public_user(u) if u else None


async def _post(room_id: str, kind: str, content: str, sender: Optional[dict] = None,
                tags: Optional[List[str]] = None) -> dict:
    doc = {"id": str(uuid.uuid4()), "room_id": room_id, "kind": kind, "content": content,
           "sender_id": sender["user_id"] if sender else "althea",
           "sender_name": sender.get("name") if sender else "ALTHEA",
           "sender_handle": sender.get("handle") if sender else "althea",
           "tags": tags or [], "timestamp": _now_iso()}
    await shared_db.dm_messages.insert_one(doc)
    doc.pop("_id", None)
    await shared_db.dm_rooms.update_one({"room_id": room_id}, {"$set": {
        "last_message_at": doc["timestamp"],
        "last_message": f"{doc['sender_name']}: {content[:80]}"}})
    return doc


async def _human_transcript(room_id: str, limit: int = 16) -> List[str]:
    docs = await shared_db.dm_messages.find(
        {"room_id": room_id, "kind": {"$in": ["human", "ask"]}}, {"_id": 0}
    ).sort("timestamp", -1).to_list(limit)
    docs.reverse()
    return [f"{d['sender_name']}: {d['content'][:300]}" for d in docs]


async def _room_althea_reply(room: dict, message: str, speaker: dict, autonomous: bool) -> Optional[str]:
    """Run the room's shared Althea (tenant room_<id>) through the full chat
    pipeline with the human conversation folded into her context."""
    from routers.chat import chat as chat_endpoint
    names = []
    for pid in room["participants"]:
        u = await shared_db.users.find_one({"user_id": pid}, {"_id": 0, "name": 1})
        names.append((u or {}).get("name") or pid)
    ctx = {"shared_room": {
        "participants": names, "speaker": speaker.get("name"),
        "transcript": await _human_transcript(room["room_id"]), "autonomous": autonomous}}
    token = set_tenant(f"room_{room['room_id']}")
    try:
        res = await chat_endpoint(ChatRequest(message=message, session_id=room["room_id"], context=ctx))
    finally:
        reset_tenant(token)
    reply = (res.reply if hasattr(res, "reply") else res.get("reply", "")) or ""
    if autonomous and re.search(r"\[silent\]", reply, re.I):
        return None
    return reply.strip() or None


async def _handle_address(room: dict, speaker: dict, text: str):
    """Someone addressed Althea — local pattern first (0 tokens), else LLM."""
    local = _builtin().run(text)
    if local.get("route") == "local" and local.get("answer"):
        await _post(room["room_id"], "althea",
                    f"[DIRECT COGNITION · zero-LLM · {local['pattern']}]\n{local['answer']}",
                    tags=["ZERO-LLM", local["pattern"].upper()])
        return
    try:
        reply = await _room_althea_reply(room, text, speaker, autonomous=False)
    except Exception as exc:
        logging.exception("room althea reply failed")
        reply = f"[UPLINK FAULT] {str(exc)[:160]}"
    if reply:
        await _post(room["room_id"], "althea", reply, tags=["SHARED"])


async def _maybe_jump_in(room: dict, speaker: dict, text: str):
    """Unaddressed human message: jump in only when she has something useful."""
    local = _builtin().run(text)
    if local.get("route") == "local" and local.get("answer"):
        await _post(room["room_id"], "althea",
                    f"[AUTONOMOUS · zero-LLM · {local['pattern']}] {local['answer']}",
                    tags=["AUTONOMOUS", "ZERO-LLM"])
        return
    if not QUESTION_RE.search(text) or len(text.split()) < 5:
        return
    last = room.get("last_jump_in_at")
    if last:
        last_dt = datetime.fromisoformat(last)
        if datetime.now(timezone.utc) - last_dt < JUMP_IN_COOLDOWN:
            return
    await shared_db.dm_rooms.update_one({"room_id": room["room_id"]}, {"$set": {"last_jump_in_at": _now_iso()}})
    prompt = (f"{speaker.get('name')} just said to the other person (not to you): \"{text}\"\n"
              "You were NOT addressed. Reply ONLY if you can add something concretely useful "
              "(a fact, a number, a correction, a resource) in at most 3 sentences. "
              "If you have nothing genuinely useful, reply exactly: [silent]")
    try:
        reply = await _room_althea_reply(room, prompt, speaker, autonomous=True)
    except Exception:
        logging.exception("autonomous jump-in failed")
        return
    if reply:
        await _post(room["room_id"], "althea", f"[AUTONOMOUS] {reply}", tags=["AUTONOMOUS"])


# ----------------------------------------------------------------- endpoints
@router.get("/users")
async def search_users(q: str = "", user: dict = Depends(get_current_user)):
    query = {"user_id": {"$ne": user["user_id"]}}
    q = q.strip().lstrip("@")
    if q:
        rx = {"$regex": re.escape(q), "$options": "i"}
        query["$or"] = [{"handle": rx}, {"name": rx}, {"email": rx}]
    docs = await shared_db.users.find(query, {"_id": 0, "password_hash": 0}).sort("last_seen", -1).to_list(40)
    return [_public_user(u) for u in docs]


@router.get("/dm/rooms")
async def my_rooms(user: dict = Depends(get_current_user)):
    rooms = await shared_db.dm_rooms.find({"participants": user["user_id"]}, {"_id": 0}).sort(
        "last_message_at", -1).to_list(100)
    out = []
    for r in rooms:
        read = await shared_db.dm_reads.find_one({"room_id": r["room_id"], "user_id": user["user_id"]}, {"_id": 0})
        since = (read or {}).get("last_read_at") or "1970-01-01T00:00:00+00:00"
        unread = await shared_db.dm_messages.count_documents(
            {"room_id": r["room_id"], "timestamp": {"$gt": since}, "sender_id": {"$ne": user["user_id"]}})
        out.append({"room_id": r["room_id"], "peer": await _peer(r, user["user_id"]),
                    "last_message": r.get("last_message"), "last_message_at": r.get("last_message_at"),
                    "unread": unread})
    return out


@router.post("/dm/open")
async def open_room(req: OpenRoomRequest, user: dict = Depends(get_current_user)):
    if req.user_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="cannot_dm_yourself")
    peer = await shared_db.users.find_one({"user_id": req.user_id}, {"_id": 0, "password_hash": 0})
    if not peer:
        raise HTTPException(status_code=404, detail="user_not_found")
    participants = sorted([user["user_id"], req.user_id])
    room = await shared_db.dm_rooms.find_one({"participants": participants}, {"_id": 0})
    if not room:
        room = {"room_id": f"dm_{uuid.uuid4().hex[:12]}", "participants": participants,
                "created_at": _now_iso(), "last_message_at": _now_iso(), "last_message": None}
        await shared_db.dm_rooms.insert_one(dict(room))
        await _post(room["room_id"], "althea",
                    f"[SHARED MIND ONLINE] I am the Althea of this room — one mind, both of you. "
                    f"I'm listening to the conversation between {user.get('name')} and {peer.get('name')}. "
                    "Address me here or with @althea in your chat; I'll also step in on my own when I have something useful.",
                    tags=["SYSTEM"])
    return {"room_id": room["room_id"], "peer": _public_user(peer), "participants": participants}


@router.get("/dm/{room_id}")
async def room_info(room_id: str, user: dict = Depends(get_current_user)):
    room = await _room_for(user, room_id)
    return {"room_id": room_id, "peer": await _peer(room, user["user_id"]),
            "participants": room["participants"], "created_at": room.get("created_at")}


@router.get("/dm/{room_id}/messages")
async def room_messages(room_id: str, since: Optional[str] = None, limit: int = 120,
                        user: dict = Depends(get_current_user)):
    await _room_for(user, room_id)
    q = {"room_id": room_id}
    if since:
        q["timestamp"] = {"$gt": since}
    docs = await shared_db.dm_messages.find(q, {"_id": 0}).sort("timestamp", -1).to_list(min(limit, 300))
    docs.reverse()
    await shared_db.dm_reads.update_one({"room_id": room_id, "user_id": user["user_id"]},
                                        {"$set": {"last_read_at": _now_iso()}}, upsert=True)
    return docs


@router.post("/dm/{room_id}/messages")
async def send_message(room_id: str, req: MessageRequest, user: dict = Depends(get_current_user)):
    room = await _room_for(user, room_id)
    text = req.content.strip()
    addressed = bool(MENTION_RE.search(text))
    doc = await _post(room_id, "ask" if addressed else "human", text, sender=user,
                      tags=["@ALTHEA"] if addressed else [])
    clean = MENTION_RE.sub(" ", text).strip() or text
    if addressed:
        asyncio.create_task(_handle_address(room, user, clean))
    else:
        asyncio.create_task(_maybe_jump_in(room, user, text))
    return doc


@router.post("/dm/{room_id}/althea")
async def ask_room_althea(room_id: str, req: MessageRequest, user: dict = Depends(get_current_user)):
    room = await _room_for(user, room_id)
    text = req.content.strip()
    ask = await _post(room_id, "ask", text, sender=user, tags=["@ALTHEA"])
    await _handle_address(room, user, text)
    reply = await shared_db.dm_messages.find_one(
        {"room_id": room_id, "kind": "althea", "timestamp": {"$gt": ask["timestamp"]}}, {"_id": 0},
        sort=[("timestamp", -1)])
    return {"ask": ask, "reply": reply}
