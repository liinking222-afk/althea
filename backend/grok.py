"""Grok (xAI) — legal bring-your-own-key engine for Althea.

Each user connects their own xAI API key (console.x.ai). The key is Fernet-
encrypted at rest on the shared `users` document, never returned to the
browser, and only ever used server-side against https://api.x.ai/v1.
Althea can run on Grok as an alternate brain (same memory, same persona);
in a direct-message room the shared Althea may borrow a participant's key
when that participant opted in (`grok_room_share`).
"""
import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

from core import current_tenant, shared_db

XAI_BASE = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4.7"
KNOWN_MODELS = ["grok-4.7", "grok-4.6", "grok-4.5", "grok-4-latest", "grok-4-fast", "grok-3"]
KEY_FIELDS = {"_id": 0, "user_id": 1, "name": 1, "xai_api_key_enc": 1, "xai_key_last4": 1,
              "xai_key_valid": 1, "ai_engine": 1, "grok_model": 1, "grok_room_share": 1}


def _fernet() -> Fernet:
    return Fernet(os.environ["FERNET_KEY"].encode())


def encrypt_key(value: str) -> str:
    return _fernet().encrypt(value.strip().encode()).decode()


def decrypt_key(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        raise HTTPException(status_code=500, detail="Stored Grok key cannot be decrypted")


def _upstream_error(status: int) -> HTTPException:
    if status == 401:
        return HTTPException(status_code=422, detail="Invalid or expired xAI API key")
    if status == 403:
        return HTTPException(status_code=403, detail="This xAI key/team is not permitted to use the API")
    if status == 429:
        return HTTPException(status_code=429, detail="xAI rate limit reached — retry shortly")
    if status == 402:
        return HTTPException(status_code=402, detail="xAI credits or billing limit insufficient")
    if status == 404:
        return HTTPException(status_code=400, detail="xAI model or endpoint not found")
    return HTTPException(status_code=502, detail=f"xAI request failed ({status})")


async def xai_request(api_key: str, method: str, path: str, **kwargs) -> httpx.Response:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(base_url=XAI_BASE, timeout=httpx.Timeout(120.0, connect=10.0)) as c:
        for attempt in range(3):
            r = await c.request(method, path, headers=headers, **kwargs)
            if r.status_code != 429 or attempt == 2:
                break
            await asyncio.sleep(min(2 ** attempt, 8))
    if r.is_error:
        logging.warning("xai upstream %s %s -> %s", method, path, r.status_code)
        raise _upstream_error(r.status_code)
    return r


async def grok_complete(api_key: str, system_prompt: str, user_text: str,
                        model: str = DEFAULT_MODEL, max_tokens: int = 1800) -> str:
    r = await xai_request(api_key, "POST", "/chat/completions", json={
        "model": model,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_text}],
        "max_tokens": max_tokens,
    })
    data = r.json()
    return ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""


async def list_models(api_key: str) -> list:
    r = await xai_request(api_key, "GET", "/models")
    ids = [m.get("id") for m in (r.json().get("data") or []) if m.get("id")]
    return sorted([i for i in ids if i.startswith("grok")]) or KNOWN_MODELS


def public_status(u: Optional[dict]) -> dict:
    u = u or {}
    return {"configured": bool(u.get("xai_api_key_enc")), "valid": bool(u.get("xai_key_valid")),
            "last4": u.get("xai_key_last4"), "engine": u.get("ai_engine") or "claude",
            "model": u.get("grok_model") or DEFAULT_MODEL,
            "room_share": u.get("grok_room_share", True)}


async def user_grok(user_id: str) -> Optional[dict]:
    u = await shared_db.users.find_one({"user_id": user_id}, KEY_FIELDS)
    if u and u.get("xai_api_key_enc") and u.get("xai_key_valid"):
        return u
    return None


async def resolve_engine() -> Optional[dict]:
    """Which brain should the CURRENT tenant's Althea think with?
    Returns {"kind": "grok", "api_key", "model", "owner"} or None (Claude)."""
    tenant = current_tenant()
    if not tenant:
        return None
    if tenant.startswith("room_"):
        room = await shared_db.dm_rooms.find_one({"room_id": tenant[5:]}, {"_id": 0})
        if not room or room.get("althea_engine") != "grok":
            return None
        for pid in room.get("participants", []):
            u = await user_grok(pid)
            if u and u.get("grok_room_share", True):
                return {"kind": "grok", "api_key": decrypt_key(u["xai_api_key_enc"]),
                        "model": u.get("grok_model") or DEFAULT_MODEL, "owner": u.get("name") or pid}
        return None
    u = await user_grok(tenant)
    if u and u.get("ai_engine") == "grok":
        return {"kind": "grok", "api_key": decrypt_key(u["xai_api_key_enc"]),
                "model": u.get("grok_model") or DEFAULT_MODEL, "owner": u.get("name") or tenant}
    return None


async def room_grok_availability(room: dict) -> dict:
    """Who in this room can lend Grok to the shared Althea."""
    lenders = []
    for pid in room.get("participants", []):
        u = await user_grok(pid)
        if u and u.get("grok_room_share", True):
            lenders.append({"user_id": pid, "name": u.get("name"), "model": u.get("grok_model") or DEFAULT_MODEL})
    return {"engine": room.get("althea_engine") or "claude", "grok_available": bool(lenders), "lenders": lenders}


async def mark_used(user_id: str):
    await shared_db.users.update_one({"user_id": user_id}, {"$set": {"xai_last_used_at": datetime.now(timezone.utc)}})
