"""Iteration 20 — DOCUMENT FORGE + server-side autonomy + regressions.

Budget: 1 LLM chat call (letter). Everything else reuses history or is
non-LLM.
"""
import os
import time
import pytest
import requests

with open("/app/frontend/.env") as f:
    for line in f:
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------- FORGE: live letter LLM call (auto-close guard) ----------
def test_forge_letter_chat(s):
    r = s.post(
        f"{API}/chat",
        json={
            "message": "Compose a complete formal letter: to the mayor requesting more park benches",
            "session_id": "test-forge-letter",
        },
        timeout=180,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    reply = d.get("reply") or ""
    tags = d.get("tags") or []
    # Local-core fallback (budget) → forge markers may be absent; skip
    if "LOCAL-CORE" in tags or "BUDGET-EXHAUSTED" in tags:
        pytest.skip(f"budget/local-core fallback: tags={tags}")
    assert "[LETTER]" in reply, reply[:400]
    assert "[/LETTER]" in reply, reply[-400:]
    assert "FORGE" in tags, tags


# ---------- FORGE: earlier blueprint session persisted ----------
def test_forge_blueprint_history(s):
    r = s.get(f"{API}/chat/history/test-forge-1", timeout=15)
    assert r.status_code == 200
    turns = r.json()
    assert isinstance(turns, list)
    if not turns:
        pytest.skip("no prior test-forge-1 session — main agent context lost")
    joined = " ".join((t.get("content") or "") for t in turns)
    assert "[BLUEPRINT" in joined, joined[:400]


# ---------- Workers mesh: server-side autonomy ----------
def test_workers_autonomy(s):
    r = s.get(f"{API}/workers", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d.get("loop_running") is True
    cores = d.get("cores") or d.get("workers") or []
    assert len(cores) == 8, len(cores)

    # Find evo/growth/diagnostic cores by name substring
    def find(name_sub):
        for c in cores:
            n = (c.get("name") or c.get("id") or "").lower()
            if name_sub in n:
                return c
        return None

    evo = find("evol")
    grow = find("growth") or find("spawn")
    diag = find("diag")
    assert evo and grow and diag, [c.get("name") for c in cores]

    for core, allowed in (
        (evo, ("EVOLVED", "gated", "cooldown", "dormant", "evolve", "idle")),
        (grow, ("SPAWNED", "gated", "cooldown", "dormant", "spawn", "idle")),
        (diag, ("nominal", "REPAIR", "repair", "ok", "idle")),
    ):
        msg = (core.get("last_task") or core.get("last_message") or core.get("status") or "")
        assert any(a.lower() in msg.lower() for a in allowed), (core.get("name"), msg)


# ---------- Regression (no new LLM calls) ----------
def test_autosynth_history_persists(s):
    r = s.get(f"{API}/chat/history/test-e2e-autosynth", timeout=15)
    assert r.status_code == 200
    turns = r.json()
    if not turns:
        pytest.skip("no prior autosynth session")
    joined = " ".join((t.get("content") or "") for t in turns)
    assert "[SYNTH-IMAGE:" in joined


def test_neural_protocol(s):
    r = s.get(f"{API}/neural/protocol", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert str(d.get("protocol", d.get("name", ""))).startswith("ANIP")


def test_web_status_online(s):
    r = s.get(f"{API}/web/status", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d.get("online") is True or str(d.get("uplink", "")).lower() == "online" or str(d.get("status", "")).lower() == "online"


def test_diagnostics_verdict(s):
    r = s.get(f"{API}/diagnostics", timeout=20)
    assert r.status_code == 200
    assert "verdict" in r.json()
