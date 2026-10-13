"""Iteration 23 — multi-user Althea: auth, per-user tenancy, direct messages + shared room Althea."""
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"
FOUNDER = {"email": "founder@althea.ai", "password": "Althea-Founder-2026!"}
ADA = {"email": "ada@example.com", "password": "Ada-Test-2026!"}


def _session(creds):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, r.text
    s.headers["Authorization"] = f"Bearer {r.json()['token']}"
    return s, r.json()["user"]


@pytest.fixture(scope="module")
def founder():
    return _session(FOUNDER)


@pytest.fixture(scope="module")
def ada():
    return _session(ADA)


def test_unauthenticated_is_rejected():
    assert requests.get(f"{API}/growth/stats", timeout=15).status_code == 401
    assert requests.get(f"{API}/evolution/version", timeout=15).status_code == 401


def test_login_bad_password():
    r = requests.post(f"{API}/auth/login", json={"email": FOUNDER["email"], "password": "nope-nope-nope"}, timeout=15)
    assert r.status_code == 401


def test_register_new_user_and_me():
    email = f"t{uuid.uuid4().hex[:8]}@example.com"
    r = requests.post(f"{API}/auth/register", json={"email": email, "password": "Strong-Pass-123", "name": "Temp User"}, timeout=20)
    assert r.status_code == 200
    tok = r.json()["token"]
    me = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {tok}"}, timeout=15).json()
    assert me["email"] == email and "password_hash" not in me
    dup = requests.post(f"{API}/auth/register", json={"email": email, "password": "Strong-Pass-123", "name": "Dup"}, timeout=20)
    assert dup.status_code == 409


def test_cookie_session_works(founder):
    s, _ = founder
    plain = requests.Session()
    r = plain.post(f"{API}/auth/login", json=FOUNDER, timeout=20)
    assert "session_token" in r.cookies or r.status_code == 200
    me = plain.get(f"{API}/auth/me", timeout=15)
    assert me.status_code == 200


def test_tenant_isolation(founder, ada):
    fs, _ = founder
    as_, _ = ada
    fg = fs.get(f"{API}/growth/stats", timeout=20).json()
    ag = as_.get(f"{API}/growth/stats", timeout=20).json()
    assert fg["memories"] > 100 and fg["evolution_cycles"] > 100  # migrated legacy brain
    assert ag["chat_messages"] < fg["chat_messages"]
    fv = fs.get(f"{API}/evolution/version", timeout=20).json()
    av = as_.get(f"{API}/evolution/version", timeout=20).json()
    assert fv["cycles"] != av["cycles"]


def test_evolution_is_per_user(ada):
    s, user = ada
    r = s.post(f"{API}/evolution/tick", json={"trigger": "manual", "force": True, "vector": "MEMORY"}, timeout=60).json()
    assert r["evolved"] and r["verified"]
    assert os.path.exists(f"/app/althea_grown_code/{user['user_id']}")


def test_user_directory(founder):
    s, me = founder
    users = s.get(f"{API}/users", params={"q": "ada"}, timeout=15).json()
    assert any(u["handle"] == "ada" for u in users)
    assert all(u["user_id"] != me["user_id"] for u in users)


def test_dm_flow_with_shared_althea(founder, ada):
    fs, fu = founder
    as_, au = ada
    room = fs.post(f"{API}/dm/open", json={"user_id": au["user_id"]}, timeout=20).json()
    rid = room["room_id"]
    assert room["peer"]["user_id"] == au["user_id"]
    # human message with a local-pattern question → Althea jumps in with zero LLM
    m = fs.post(f"{API}/dm/{rid}/messages", json={"content": f"Ada, what is 19 * 21? ({uuid.uuid4().hex[:4]})"}, timeout=20).json()
    assert m["kind"] == "human"
    time.sleep(1.5)
    msgs = as_.get(f"{API}/dm/{rid}/messages", timeout=20).json()
    assert any(x["kind"] == "althea" and "399" in x["content"] for x in msgs)
    # @althea mention is stored as "ask" and answered
    a = as_.post(f"{API}/dm/{rid}/messages", json={"content": "@althea convert 3 km to miles"}, timeout=20).json()
    assert a["kind"] == "ask"
    time.sleep(1.5)
    msgs = fs.get(f"{API}/dm/{rid}/messages", params={"since": a["timestamp"]}, timeout=20).json()
    assert any(x["kind"] == "althea" and "1.86411" in x["content"] for x in msgs)
    # inbox shows the room for both
    assert any(r["room_id"] == rid for r in fs.get(f"{API}/dm/rooms", timeout=20).json())
    assert any(r["room_id"] == rid for r in as_.get(f"{API}/dm/rooms", timeout=20).json())


def test_dm_room_access_control(ada):
    s, _ = ada
    assert s.get(f"{API}/dm/dm_doesnotexist/messages", timeout=15).status_code == 404


def test_logout_clears_cookie_session():
    plain = requests.Session()
    plain.post(f"{API}/auth/login", json=ADA, timeout=20)
    assert plain.get(f"{API}/auth/me", timeout=15).status_code == 200
    plain.post(f"{API}/auth/logout", timeout=15)
    assert plain.get(f"{API}/auth/me", timeout=15).status_code == 401
