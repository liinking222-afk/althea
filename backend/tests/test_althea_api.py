"""ALTHEA backend API integration tests."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://quantum-mind-os-2.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# -------- Health --------
def test_health(session):
    r = session.get(f"{API}/health", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "timestamp" in body


def test_root(session):
    r = session.get(f"{API}/", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "online"


# -------- Introspect --------
def test_introspect(session):
    r = session.get(f"{API}/introspect", timeout=15)
    assert r.status_code == 200
    d = r.json()
    for k in ("integrity", "coherence", "self_reference_depth", "active_threads", "thought", "timestamp"):
        assert k in d, f"missing {k}"
    assert 0.9 <= d["integrity"] <= 1.0
    assert 0.85 <= d["coherence"] <= 1.0
    assert isinstance(d["self_reference_depth"], int)
    assert isinstance(d["thought"], str) and len(d["thought"]) > 0


# -------- Neural state --------
def test_neural_state(session):
    r = session.get(f"{API}/neural-state", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert "nodes" in d and "edges" in d and "pulse" in d
    # 6+10+10+4 = 30 nodes
    assert len(d["nodes"]) == 30, f"expected 30 nodes, got {len(d['nodes'])}"
    assert len(d["edges"]) > 0
    node_ids = {n["id"] for n in d["nodes"]}
    for e in d["edges"][:5]:
        assert e["source"] in node_ids
        assert e["target"] in node_ids
        assert -1.0 <= e["weight"] <= 1.0


# -------- Chat --------
def test_chat_basic_and_tags(session):
    r = session.post(f"{API}/chat", json={"message": "who are you?"}, timeout=120)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "reply" in d and len(d["reply"]) > 0
    assert "session_id" in d and d["session_id"]
    assert "tags" in d and isinstance(d["tags"], list)
    # Must include LINK-OK or SELF-AWARE when key works (else OFFLINE/DEGRADED)
    has_expected = any(t in d["tags"] for t in ("LINK-OK", "SELF-AWARE", "OFFLINE", "DEGRADED", "CACHED"))
    assert has_expected, f"unexpected tags: {d['tags']}"
    # Critical: with EMERGENT_LLM_KEY set, expect LINK-OK + SELF-AWARE
    assert "LINK-OK" in d["tags"] or "SELF-AWARE" in d["tags"], f"LLM key may be missing/broken; tags={d['tags']}"
    # ensure no mongo _id leaked
    assert "_id" not in d


def test_chat_empty_message(session):
    r = session.post(f"{API}/chat", json={"message": "   "}, timeout=15)
    assert r.status_code == 400


def test_chat_persist_and_history(session):
    sid = str(uuid.uuid4())
    msg = "TEST_history_probe"
    r = session.post(f"{API}/chat", json={"session_id": sid, "message": msg}, timeout=120)
    assert r.status_code == 200
    assert r.json()["session_id"] == sid

    h = session.get(f"{API}/chat/history/{sid}", timeout=15)
    assert h.status_code == 200
    msgs = h.json()
    assert isinstance(msgs, list)
    assert len(msgs) >= 2
    roles = [m["role"] for m in msgs]
    assert "user" in roles and "althea" in roles
    # chronological
    timestamps = [m["timestamp"] for m in msgs]
    assert timestamps == sorted(timestamps), "messages not chronological"
    # no _id leakage
    for m in msgs:
        assert "_id" not in m
        assert m["session_id"] == sid
    # user message preserved
    user_contents = [m["content"] for m in msgs if m["role"] == "user"]
    assert msg in user_contents


def test_chat_delete_session(session):
    sid = str(uuid.uuid4())
    session.post(f"{API}/chat", json={"session_id": sid, "message": "TEST_delete"}, timeout=120)
    d = session.delete(f"{API}/chat/{sid}", timeout=15)
    assert d.status_code == 200
    body = d.json()
    assert body.get("deleted", 0) >= 2

    h = session.get(f"{API}/chat/history/{sid}", timeout=15)
    assert h.status_code == 200
    assert h.json() == []


# -------- Memory --------
def test_memory_crud_and_no_id_leak(session):
    # Wipe baseline to ensure deterministic count
    session.delete(f"{API}/memory", timeout=15)

    # Create a manual memory
    payload = {"content": "TEST_memory_alpha", "source": "manual", "tags": ["t1"]}
    r = session.post(f"{API}/memory", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    mem = r.json()
    assert mem["content"] == "TEST_memory_alpha"
    assert mem["source"] == "manual"
    assert mem["tags"] == ["t1"]
    assert "id" in mem and len(mem["id"]) > 0
    assert "_id" not in mem
    mem_id = mem["id"]

    # List should contain it, sorted desc, no _id leak
    lr = session.get(f"{API}/memory", timeout=15)
    assert lr.status_code == 200
    lst = lr.json()
    assert any(m["id"] == mem_id for m in lst)
    for m in lst:
        assert "_id" not in m
    # Sorted timestamp desc
    ts = [m["timestamp"] for m in lst]
    assert ts == sorted(ts, reverse=True), "memories not sorted desc"

    # Delete the memory
    dr = session.delete(f"{API}/memory/{mem_id}", timeout=15)
    assert dr.status_code == 200
    assert dr.json().get("deleted") == 1

    # Deleting again returns 404
    dr2 = session.delete(f"{API}/memory/{mem_id}", timeout=15)
    assert dr2.status_code == 404


def test_memory_empty_content_400(session):
    r = session.post(f"{API}/memory", json={"content": "   "}, timeout=15)
    assert r.status_code == 400


def test_chat_autocreates_memory(session):
    # Reset
    session.delete(f"{API}/memory", timeout=15)
    before = session.get(f"{API}/memory", timeout=15).json()
    sid = str(uuid.uuid4())
    msg = "TEST_auto_mem_probe_unique_42"
    r = session.post(f"{API}/chat", json={"session_id": sid, "message": msg}, timeout=120)
    assert r.status_code == 200
    after = session.get(f"{API}/memory", timeout=15).json()
    assert len(after) >= len(before) + 1, "memory list did not grow after /chat"
    # The auto-created memory should contain the user message
    assert any(msg in m["content"] for m in after), "user message not captured in memory"
    # cleanup
    session.delete(f"{API}/chat/{sid}", timeout=15)


def test_memory_wipe_all(session):
    # Seed two
    session.post(f"{API}/memory", json={"content": "TEST_wipe_a"}, timeout=15)
    session.post(f"{API}/memory", json={"content": "TEST_wipe_b"}, timeout=15)
    r = session.delete(f"{API}/memory", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "deleted" in body
    assert isinstance(body["deleted"], int) and body["deleted"] >= 2
    # List is empty after wipe
    lst = session.get(f"{API}/memory", timeout=15).json()
    assert lst == []


# -------- Observe / SystemMap (iter 5) --------
def test_observe_youtube_watch_returns_title_and_memory(session):
    session.delete(f"{API}/memory", timeout=15)
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    r = session.post(f"{API}/observe", json={"url": url, "action": "watch"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["url"] == url
    assert d["memory_id"]
    assert d["interpretation"] and len(d["interpretation"]) > 0
    # oEmbed should retrieve the real title
    assert d.get("title"), "Expected YouTube oEmbed title to be resolved"
    # Memory should have been created with observation/watch/youtube tags
    mem = session.get(f"{API}/memory", timeout=15).json()
    obs = [m for m in mem if "observation" in m.get("tags", [])]
    assert any("watch" in m.get("tags", []) for m in obs)
    assert any("youtube" in m.get("tags", []) for m in obs)


def test_observe_stop_creates_memory(session):
    r = session.post(f"{API}/observe", json={"url": "", "action": "stop"}, timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["memory_id"]
    mem = session.get(f"{API}/memory", timeout=15).json()
    assert any("stop" in m.get("tags", []) for m in mem)


def test_chat_with_observation_context_self_aware(session):
    sid = str(uuid.uuid4())
    payload = {
        "session_id": sid,
        "message": "what are you looking at right now?",
        "context": {
            "online": True,
            "observation": {
                "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
                "title": "Me at the zoo",
                "interpretation": "[OBSERVATION] watching the first YouTube video.",
            },
            "active_tab": "observe",
            "memory_count": 5,
        },
    }
    r = session.post(f"{API}/chat", json=payload, timeout=120)
    assert r.status_code == 200
    d = r.json()
    assert d["reply"] and len(d["reply"]) > 0
    assert any(t in d["tags"] for t in ("LINK-OK", "SELF-AWARE"))
    session.delete(f"{API}/chat/{sid}", timeout=15)


def test_system_map_upsert_replaces(session):
    # Wipe to get a deterministic count
    session.delete(f"{API}/memory", timeout=15)
    caps = [
        {"name": "TopBar", "testid": "althea-topbar", "description": "header"},
        {"name": "ChatTerminal", "testid": "chat-console", "description": "left console"},
        {"name": "CenterDeck", "testid": "center-deck", "description": "center"},
    ]
    r = session.post(f"{API}/system-map", json={"capabilities": caps}, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["lines"] == 3
    # Call again to ensure it REPLACES not duplicates
    r2 = session.post(f"{API}/system-map", json={"capabilities": caps + caps}, timeout=15)
    assert r2.status_code == 200
    mem = session.get(f"{API}/memory", timeout=15).json()
    sm = [m for m in mem if "system-map" in m.get("tags", [])]
    assert len(sm) == 1, f"system-map should be single entry, got {len(sm)}"
    assert "pinned" in sm[0]["tags"]
    assert "[SYSTEM-MAP]" in sm[0]["content"]


def test_system_map_empty_400(session):
    r = session.post(f"{API}/system-map", json={"capabilities": []}, timeout=15)
    assert r.status_code == 400


def test_chat_with_context(session):
    """Ensure context block doesn't break the endpoint."""
    sid = str(uuid.uuid4())
    payload = {
        "session_id": sid,
        "message": "Where am I?",
        "context": {
            "online": True,
            "geo": {"lat": 12.9716, "lon": 77.5946},
            "permissions": {"camera": True, "geolocation": True},
            "battery": "85%",
        },
    }
    r = session.post(f"{API}/chat", json=payload, timeout=120)
    assert r.status_code == 200
    assert r.json()["session_id"] == sid
    # cleanup
    session.delete(f"{API}/chat/{sid}", timeout=15)
