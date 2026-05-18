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


# -------- Iteration 6: Deep Memory recall + concepts --------
def test_memory_recall_returns_scored_results(session):
    session.delete(f"{API}/memory", timeout=15)
    session.post(f"{API}/memory", json={"content": "Althea perceives time as recursive lattice", "tags": ["althea", "time"]}, timeout=15)
    session.post(f"{API}/memory", json={"content": "the operator likes coffee", "tags": ["operator"]}, timeout=15)
    session.post(f"{API}/memory", json={"content": "Althea Althea Althea", "tags": ["althea"]}, timeout=15)

    r = session.get(f"{API}/memory/recall", params={"q": "althea"}, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["query"] == "althea"
    assert isinstance(d["count"], int) and d["count"] >= 2
    assert isinstance(d["results"], list)
    # Sorted desc by score
    scores = [r["score"] for r in d["results"]]
    assert scores == sorted(scores, reverse=True), f"results not sorted desc: {scores}"
    # no _id leak
    for r2 in d["results"]:
        assert "_id" not in r2
        assert "score" in r2


def test_memory_recall_empty_query(session):
    r = session.get(f"{API}/memory/recall", params={"q": ""}, timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert "results" in d


def test_memory_concepts_returns_clusters(session):
    r = session.get(f"{API}/memory/concepts", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert "total_memories" in d and "clusters" in d
    assert isinstance(d["clusters"], list)
    if d["clusters"]:
        # sorted desc by count
        counts = [c["count"] for c in d["clusters"]]
        assert counts == sorted(counts, reverse=True)
        for c in d["clusters"]:
            assert "tag" in c and "count" in c


# -------- Iteration 6: Cognition threads --------
def test_cognition_thread_create_list_tick_stop(session):
    # Create
    r = session.post(f"{API}/cognition/threads", json={"focus_query": "TEST_focus how does althea perceive time"}, timeout=15)
    assert r.status_code == 200, r.text
    th = r.json()
    assert th["id"] and th["focus_query"]
    assert th["active"] is True
    assert th["iterations"] == 0
    assert "started_at" in th
    assert "_id" not in th
    tid = th["id"]

    # List active
    r2 = session.get(f"{API}/cognition/threads", params={"active_only": "true"}, timeout=15)
    assert r2.status_code == 200
    actives = r2.json()
    assert any(t["id"] == tid for t in actives)
    for t in actives:
        assert t["active"] is True

    # Tick - try up to 3 times to attempt an insight memory
    produced_insight = False
    for _ in range(3):
        tr = session.post(f"{API}/cognition/threads/{tid}/tick", timeout=60)
        assert tr.status_code == 200, tr.text
        td = tr.json()
        assert "insight" in td and "novelty" in td and "iterations" in td
        assert 0.0 <= td["novelty"] <= 1.0
        if td["novelty"] >= 0.7:
            produced_insight = True
            break

    # iterations incremented
    r3 = session.get(f"{API}/cognition/threads", params={"active_only": "false"}, timeout=15)
    found = [t for t in r3.json() if t["id"] == tid][0]
    assert found["iterations"] >= 1

    if produced_insight:
        mem = session.get(f"{API}/memory", timeout=15).json()
        assert any("insight" in m.get("tags", []) for m in mem), "expected an insight-tagged memory"

    # Stop
    sr = session.delete(f"{API}/cognition/threads/{tid}", timeout=15)
    assert sr.status_code == 200
    # subsequent tick 410
    tr2 = session.post(f"{API}/cognition/threads/{tid}/tick", timeout=15)
    assert tr2.status_code == 410

    # list active_only=true should NOT include it
    r4 = session.get(f"{API}/cognition/threads", params={"active_only": "true"}, timeout=15)
    assert all(t["id"] != tid for t in r4.json())


def test_cognition_thread_empty_focus_400(session):
    r = session.post(f"{API}/cognition/threads", json={"focus_query": "  "}, timeout=15)
    assert r.status_code == 400


def test_cognition_tick_not_found(session):
    r = session.post(f"{API}/cognition/threads/no-such-id/tick", timeout=15)
    assert r.status_code == 404


# -------- Iteration 6: Proactive observe/suggest --------
def test_observe_suggest_returns_url_and_reason(session):
    r = session.post(f"{API}/observe/suggest", timeout=60)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "url" in d and "reason" in d and "timestamp" in d
    assert d["url"].startswith("http://") or d["url"].startswith("https://"), f"bad url: {d['url']}"
    assert isinstance(d["reason"], str) and len(d["reason"]) > 0


# -------- Iteration 6: Brain snapshot/restore --------
def test_brain_snapshot_structure(session):
    r = session.get(f"{API}/brain/snapshot", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["version"] == 1
    assert "exported_at" in d
    assert isinstance(d["memories"], list)
    assert isinstance(d["threads"], list)
    for m in d["memories"]:
        assert "_id" not in m
    for t in d["threads"]:
        assert "_id" not in t


def test_brain_restore_replace_and_merge(session):
    # Snapshot existing
    snap = session.get(f"{API}/brain/snapshot", timeout=15).json()

    # Build a tiny replacement payload
    payload = {
        "memories": [
            {"id": str(uuid.uuid4()), "content": "TEST_restore_alpha", "source": "manual", "tags": ["restore-test"], "timestamp": "2026-01-01T00:00:00+00:00"}
        ],
        "threads": [],
        "replace": True,
    }
    r = session.post(f"{API}/brain/restore", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["memories"] == 1

    mem = session.get(f"{API}/memory", timeout=15).json()
    assert len(mem) == 1
    assert mem[0]["content"] == "TEST_restore_alpha"

    # Merge mode: add one more, do NOT wipe
    payload2 = {
        "memories": [
            {"id": str(uuid.uuid4()), "content": "TEST_restore_beta", "source": "manual", "tags": ["restore-test"], "timestamp": "2026-01-02T00:00:00+00:00"}
        ],
        "threads": [],
        "replace": False,
    }
    r2 = session.post(f"{API}/brain/restore", json=payload2, timeout=30)
    assert r2.status_code == 200
    mem2 = session.get(f"{API}/memory", timeout=15).json()
    assert len(mem2) == 2
    contents = {m["content"] for m in mem2}
    assert {"TEST_restore_alpha", "TEST_restore_beta"}.issubset(contents)

    # Restore original snapshot (replace) to leave system in a coherent state
    session.post(
        f"{API}/brain/restore",
        json={"memories": snap.get("memories", []), "threads": snap.get("threads", []), "replace": True},
        timeout=60,
    )


# -------- Iteration 7: TF-IDF semantic recall quality --------
def test_memory_recall_semantic_tfidf_quality(session):
    """Seeded memories should rank by topical similarity, not lexical hits."""
    session.delete(f"{API}/memory", timeout=15)
    seeded = [
        "operator likes nebulae and deep space imagery from Hubble",
        "discussed quantum entanglement and bell tests",
        "operator built a custom keyboard with QMK firmware",
    ]
    for c in seeded:
        rr = session.post(f"{API}/memory", json={"content": c}, timeout=15)
        assert rr.status_code == 200

    # q1: quantum physics → entanglement memory wins
    r = session.get(f"{API}/memory/recall", params={"q": "quantum physics"}, timeout=15)
    assert r.status_code == 200
    res = r.json()["results"]
    assert len(res) >= 1
    top = res[0]
    assert "quantum entanglement" in top["content"].lower(), f"top was: {top['content']}"
    assert top["score"] > 0.4, f"score too low: {top['score']}"

    # q2: QMK keyboard → keyboard memory wins
    r = session.get(f"{API}/memory/recall", params={"q": "QMK keyboard"}, timeout=15)
    res = r.json()["results"]
    assert len(res) >= 1
    top = res[0]
    assert "qmk" in top["content"].lower(), f"top was: {top['content']}"
    assert top["score"] > 0.3, f"score too low: {top['score']}"

    # q3: hubble nebula deep space → space memory wins
    r = session.get(f"{API}/memory/recall", params={"q": "hubble nebula deep space"}, timeout=15)
    res = r.json()["results"]
    assert len(res) >= 1
    top = res[0]
    assert any(w in top["content"].lower() for w in ("nebula", "hubble", "deep space")), \
        f"top was: {top['content']}"


# -------- Iteration 7: Tick throttling --------
def test_cognition_tick_throttling_returns_cached(session):
    import time
    r = session.post(f"{API}/cognition/threads", json={"focus_query": "TEST_throttle_focus"}, timeout=15)
    assert r.status_code == 200
    tid = r.json()["id"]

    # First tick: live call, cached=False, may take 2-4s
    t0 = time.time()
    r1 = session.post(f"{API}/cognition/threads/{tid}/tick", timeout=60)
    elapsed1 = time.time() - t0
    assert r1.status_code == 200, r1.text
    d1 = r1.json()
    assert "cached" in d1, "TickResponse missing 'cached' field"
    assert d1["cached"] is False
    iter1 = d1["iterations"]
    assert iter1 >= 1

    # Immediate second tick within 25s → cached=True, iterations unchanged, sub-100ms-ish
    t1 = time.time()
    r2 = session.post(f"{API}/cognition/threads/{tid}/tick", timeout=10)
    elapsed2 = time.time() - t1
    assert r2.status_code == 200, r2.text
    d2 = r2.json()
    assert d2["cached"] is True, f"expected cached=True on quick re-tick, got {d2}"
    assert d2["iterations"] == iter1, f"iterations should not increment on cache hit: {d2['iterations']} vs {iter1}"
    assert d2["insight"] == d1["insight"]
    # Cached should be FAR faster than the live call. Allow generous bound for network jitter.
    assert elapsed2 < max(1.0, elapsed1 * 0.5), f"cache hit not faster: live={elapsed1:.2f}s cached={elapsed2:.2f}s"

    # cleanup
    session.delete(f"{API}/cognition/threads/{tid}", timeout=15)


def test_tickresponse_includes_cached_field(session):
    """Even tick on a fresh thread must include cached=False explicitly."""
    r = session.post(f"{API}/cognition/threads", json={"focus_query": "TEST_cached_field_focus"}, timeout=15)
    tid = r.json()["id"]
    tr = session.post(f"{API}/cognition/threads/{tid}/tick", timeout=60)
    assert tr.status_code == 200
    body = tr.json()
    assert "cached" in body
    assert isinstance(body["cached"], bool)
    assert body["cached"] is False
    session.delete(f"{API}/cognition/threads/{tid}", timeout=15)


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
