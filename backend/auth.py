"""Authentication core — email/password (bcrypt + JWT) and Emergent Google
sessions share one `users` collection and one cookie (`session_token`).

Resolution order for a request: cookie `session_token` → `Authorization:
Bearer`. The token is either an opaque Google session (looked up in
`user_sessions`) or a signed JWT issued at email/password login.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import httpx
import jwt
from fastapi import HTTPException, Request

from core import shared_db

JWT_ALGORITHM = "HS256"
SESSION_DAYS = 7
COOKIE_NAME = "session_token"
EMERGENT_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
PUBLIC_FIELDS = {"_id": 0, "password_hash": 0}


def _secret() -> str:
    return os.environ["JWT_SECRET"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def new_user_id() -> str:
    return f"user_{uuid.uuid4().hex[:12]}"


def handle_from_email(email: str) -> str:
    base = "".join(c for c in email.split("@", 1)[0].lower() if c.isalnum() or c in "._-")[:24]
    return base or "operator"


def create_jwt(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "type": "access",
               "exp": datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)}
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


async def create_session(user_id: str, session_token: Optional[str] = None) -> str:
    token = session_token or f"sess_{uuid.uuid4().hex}"
    await shared_db.user_sessions.insert_one({
        "user_id": user_id, "session_token": token,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS),
        "created_at": datetime.now(timezone.utc),
    })
    return token


def set_session_cookie(response, token: str):
    response.set_cookie(key=COOKIE_NAME, value=token, httponly=True, secure=True,
                        samesite="none", max_age=SESSION_DAYS * 86400, path="/")


def clear_session_cookie(response):
    response.delete_cookie(key=COOKIE_NAME, path="/", secure=True, samesite="none")


def extract_token(request: Request) -> Optional[str]:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip() or None
    return None


async def user_from_token(token: str) -> Optional[dict]:
    if not token:
        return None
    sess = await shared_db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if sess:
        exp = sess["expires_at"]
        if isinstance(exp, str):
            exp = datetime.fromisoformat(exp)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            await shared_db.user_sessions.delete_one({"session_token": token})
            return None
        return await shared_db.users.find_one({"user_id": sess["user_id"]}, PUBLIC_FIELDS)
    try:
        payload = jwt.decode(token, _secret(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    return await shared_db.users.find_one({"user_id": payload.get("sub")}, PUBLIC_FIELDS)


async def resolve_user(request: Request) -> Optional[dict]:
    return await user_from_token(extract_token(request))


async def get_current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None) or await resolve_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def exchange_emergent_session(session_id: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(EMERGENT_SESSION_URL, headers={"X-Session-ID": session_id})
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired Google session")
    return r.json()


async def upsert_google_user(data: dict) -> dict:
    email = (data.get("email") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")
    existing = await shared_db.users.find_one({"email": email}, PUBLIC_FIELDS)
    now = datetime.now(timezone.utc)
    if existing:
        await shared_db.users.update_one({"email": email}, {"$set": {
            "name": data.get("name") or existing.get("name"),
            "picture": data.get("picture") or existing.get("picture"),
            "last_login_at": now}, "$addToSet": {"providers": "google"}})
        return await shared_db.users.find_one({"email": email}, PUBLIC_FIELDS)
    doc = {"user_id": new_user_id(), "email": email, "name": data.get("name") or email.split("@")[0],
           "handle": await unique_handle(handle_from_email(email)), "picture": data.get("picture"),
           "providers": ["google"], "role": "member", "created_at": now, "last_login_at": now,
           "last_seen": now}
    await shared_db.users.insert_one(doc)
    return await shared_db.users.find_one({"email": email}, PUBLIC_FIELDS)


async def unique_handle(base: str) -> str:
    handle, n = base, 1
    while await shared_db.users.find_one({"handle": handle}, {"_id": 1}):
        n += 1
        handle = f"{base}{n}"
    return handle


async def ensure_indexes():
    await shared_db.users.create_index("email", unique=True)
    await shared_db.users.create_index("user_id", unique=True)
    await shared_db.users.create_index("handle")
    await shared_db.user_sessions.create_index("session_token", unique=True)
    await shared_db.user_sessions.create_index("expires_at", expireAfterSeconds=0)
    await shared_db.login_attempts.create_index("identifier")
    await shared_db.dm_messages.create_index([("room_id", 1), ("timestamp", 1)])
    await shared_db.dm_rooms.create_index("participants")


async def seed_founder() -> Optional[dict]:
    email = (os.environ.get("ADMIN_EMAIL") or "").lower().strip()
    password = os.environ.get("ADMIN_PASSWORD") or ""
    if not email or not password:
        return None
    existing = await shared_db.users.find_one({"email": email})
    now = datetime.now(timezone.utc)
    if existing is None:
        doc = {"user_id": new_user_id(), "email": email, "name": "Founder",
               "handle": await unique_handle("founder"), "picture": None,
               "providers": ["password"], "role": "founder", "password_hash": hash_password(password),
               "created_at": now, "last_seen": now}
        await shared_db.users.insert_one(doc)
    elif not existing.get("password_hash") or not verify_password(password, existing["password_hash"]):
        await shared_db.users.update_one({"email": email}, {
            "$set": {"password_hash": hash_password(password), "role": "founder"},
            "$addToSet": {"providers": "password"}})
    return await shared_db.users.find_one({"email": email}, PUBLIC_FIELDS)
