"""Auth endpoints — /api/auth/*  (email+password JWT and Emergent Google)."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field

from auth import (
    PUBLIC_FIELDS,
    clear_session_cookie,
    create_jwt,
    create_session,
    exchange_emergent_session,
    extract_token,
    get_current_user,
    handle_from_email,
    hash_password,
    new_user_id,
    set_session_cookie,
    unique_handle,
    upsert_google_user,
    verify_password,
)
from core import shared_db

router = APIRouter(prefix="/auth")

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=60)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SessionExchangeRequest(BaseModel):
    session_id: str


class ChangePasswordRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: str = Field(min_length=8, max_length=128)


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=60)
    handle: Optional[str] = Field(default=None, min_length=2, max_length=24, pattern=r"^[a-z0-9._-]+$")


def _ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    return (fwd.split(",")[0].strip() if fwd else request.client.host if request.client else "?")


async def _check_lockout(identifier: str):
    doc = await shared_db.login_attempts.find_one({"identifier": identifier}, {"_id": 0})
    if not doc:
        return
    locked_until = doc.get("locked_until")
    if locked_until:
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until > datetime.now(timezone.utc):
            mins = int((locked_until - datetime.now(timezone.utc)).total_seconds() // 60) + 1
            raise HTTPException(status_code=429, detail=f"Too many attempts. Try again in {mins} min.")


async def _record_failure(identifier: str):
    doc = await shared_db.login_attempts.find_one({"identifier": identifier}, {"_id": 0})
    count = (doc or {}).get("count", 0) + 1
    update = {"count": count, "last_at": datetime.now(timezone.utc)}
    if count >= MAX_ATTEMPTS:
        update["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        update["count"] = 0
    await shared_db.login_attempts.update_one({"identifier": identifier}, {"$set": update}, upsert=True)


def _public(user: dict) -> dict:
    return {k: v for k, v in user.items() if k not in ("password_hash", "_id")}


async def _issue(response: Response, user: dict, via: str) -> dict:
    token = create_jwt(user["user_id"], user["email"]) if via == "password" \
        else await create_session(user["user_id"])
    set_session_cookie(response, token)
    await shared_db.users.update_one({"user_id": user["user_id"]}, {"$set": {
        "last_login_at": datetime.now(timezone.utc), "last_seen": datetime.now(timezone.utc)}})
    return {"user": _public(user), "token": token}


@router.post("/register")
async def register(req: RegisterRequest, response: Response):
    email = req.email.lower().strip()
    if await shared_db.users.find_one({"email": email}, {"_id": 1}):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    now = datetime.now(timezone.utc)
    doc = {"user_id": new_user_id(), "email": email, "name": req.name.strip(),
           "handle": await unique_handle(handle_from_email(email)), "picture": None,
           "providers": ["password"], "role": "member", "password_hash": hash_password(req.password),
           "created_at": now, "last_seen": now}
    await shared_db.users.insert_one(doc)
    user = await shared_db.users.find_one({"email": email}, PUBLIC_FIELDS)
    return await _issue(response, user, "password")


@router.post("/login")
async def login(req: LoginRequest, request: Request, response: Response):
    email = req.email.lower().strip()
    identifier = f"{_ip(request)}:{email}"
    await _check_lockout(identifier)
    user = await shared_db.users.find_one({"email": email})
    if not user or not user.get("password_hash") or not verify_password(req.password, user["password_hash"]):
        await _record_failure(identifier)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await shared_db.login_attempts.delete_one({"identifier": identifier})
    return await _issue(response, user, "password")


@router.post("/session")
async def google_session(req: SessionExchangeRequest, response: Response):
    """Exchange the Emergent `session_id` (URL fragment) for a 7-day session."""
    data = await exchange_emergent_session(req.session_id)
    user = await upsert_google_user(data)
    token = data.get("session_token") or None
    token = await create_session(user["user_id"], token)
    set_session_cookie(response, token)
    return {"user": _public(user), "token": token}


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = extract_token(request)
    if token:
        await shared_db.user_sessions.delete_one({"session_token": token})
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return _public(user)


@router.patch("/me")
async def update_me(req: ProfileUpdate, user: dict = Depends(get_current_user)):
    update = {}
    if req.name:
        update["name"] = req.name.strip()
    if req.handle:
        clash = await shared_db.users.find_one({"handle": req.handle, "user_id": {"$ne": user["user_id"]}}, {"_id": 1})
        if clash:
            raise HTTPException(status_code=409, detail="Handle already taken")
        update["handle"] = req.handle
    if update:
        await shared_db.users.update_one({"user_id": user["user_id"]}, {"$set": update})
    return _public(await shared_db.users.find_one({"user_id": user["user_id"]}, PUBLIC_FIELDS))


@router.post("/change-password")
async def change_password(req: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    full = await shared_db.users.find_one({"user_id": user["user_id"]})
    if full.get("password_hash"):
        if not req.current_password or not verify_password(req.current_password, full["password_hash"]):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
    await shared_db.users.update_one({"user_id": user["user_id"]}, {
        "$set": {"password_hash": hash_password(req.new_password)},
        "$addToSet": {"providers": "password"}})
    logging.info("password changed for %s", user["email"])
    return {"ok": True}
