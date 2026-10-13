"""Grok endpoints — /api/grok/*  (BYOK xAI key, engine selection, direct ask)."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from core import shared_db
from grok import (
    DEFAULT_MODEL,
    KEY_FIELDS,
    KNOWN_MODELS,
    decrypt_key,
    encrypt_key,
    grok_complete,
    list_models,
    mark_used,
    public_status,
    xai_request,
)
from system_prompt import ALTHEA_SYSTEM_PROMPT

router = APIRouter(prefix="/grok")


class KeyRequest(BaseModel):
    api_key: str = Field(min_length=20, max_length=300)


class EngineRequest(BaseModel):
    engine: Optional[str] = None  # claude | grok
    model: Optional[str] = None
    room_share: Optional[bool] = None


class AskRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    as_althea: bool = False


async def _me(user: dict) -> dict:
    return await shared_db.users.find_one({"user_id": user["user_id"]}, KEY_FIELDS) or {}


@router.get("/status")
async def status(user: dict = Depends(get_current_user)):
    return public_status(await _me(user))


@router.post("/key")
async def save_key(req: KeyRequest, user: dict = Depends(get_current_user)):
    key = req.api_key.strip()
    try:
        await xai_request(key, "POST", "/chat/completions", json={
            "model": DEFAULT_MODEL,
            "messages": [{"role": "user", "content": "Reply with OK."}],
            "max_tokens": 4})
    except HTTPException:
        await shared_db.users.update_one({"user_id": user["user_id"]}, {"$set": {"xai_key_valid": False}})
        raise
    await shared_db.users.update_one({"user_id": user["user_id"]}, {"$set": {
        "xai_api_key_enc": encrypt_key(key), "xai_key_last4": key[-4:], "xai_key_valid": True,
        "xai_validated_at": datetime.now(timezone.utc),
        "grok_model": (await _me(user)).get("grok_model") or DEFAULT_MODEL}})
    return public_status(await _me(user))


@router.delete("/key")
async def delete_key(user: dict = Depends(get_current_user)):
    await shared_db.users.update_one({"user_id": user["user_id"]}, {
        "$unset": {"xai_api_key_enc": "", "xai_key_last4": "", "xai_key_valid": "", "xai_validated_at": ""},
        "$set": {"ai_engine": "claude"}})
    return public_status(await _me(user))


@router.get("/models")
async def models(user: dict = Depends(get_current_user)):
    me = await _me(user)
    if not me.get("xai_api_key_enc"):
        return {"models": KNOWN_MODELS, "live": False}
    try:
        return {"models": await list_models(decrypt_key(me["xai_api_key_enc"])), "live": True}
    except HTTPException:
        return {"models": KNOWN_MODELS, "live": False}


@router.post("/engine")
async def set_engine(req: EngineRequest, user: dict = Depends(get_current_user)):
    me = await _me(user)
    update = {}
    if req.engine is not None:
        if req.engine not in ("claude", "grok"):
            raise HTTPException(status_code=400, detail="engine must be claude or grok")
        if req.engine == "grok" and not (me.get("xai_api_key_enc") and me.get("xai_key_valid")):
            raise HTTPException(status_code=400, detail="Connect a valid xAI key before switching to Grok")
        update["ai_engine"] = req.engine
    if req.model is not None:
        if not req.model.startswith("grok"):
            raise HTTPException(status_code=400, detail="Unsupported Grok model")
        update["grok_model"] = req.model
    if req.room_share is not None:
        update["grok_room_share"] = bool(req.room_share)
    if update:
        await shared_db.users.update_one({"user_id": user["user_id"]}, {"$set": update})
    return public_status(await _me(user))


@router.post("/ask")
async def ask(req: AskRequest, user: dict = Depends(get_current_user)):
    """Direct Grok answer with the user's own key — Grok speaking as Grok,
    working alongside Althea (not through her memory)."""
    me = await _me(user)
    if not (me.get("xai_api_key_enc") and me.get("xai_key_valid")):
        raise HTTPException(status_code=400, detail="Connect your xAI key first (/grok connect)")
    model = me.get("grok_model") or DEFAULT_MODEL
    system = (ALTHEA_SYSTEM_PROMPT if req.as_althea else
              "You are Grok, built by xAI, operating as a second mind alongside ALTHEA inside her terminal. "
              f"The user is {user.get('name')}. Be sharp, direct, witty, concise. Plain text or light markdown.")
    text = await grok_complete(decrypt_key(me["xai_api_key_enc"]), system, req.message, model=model)
    await mark_used(user["user_id"])
    return {"reply": text, "model": model, "engine": "grok"}
