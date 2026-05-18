"""Regression: Iteration 14 — Infinite Growth + Upgraded Terminal.

Run with:
    cd /app/backend && python -m pytest tests/test_iter14.py -v
"""
import os

import httpx
import pytest

BASE = os.environ.get(
    "ALTHEA_API_URL",
    "https://quantum-mind-os-2.preview.emergentagent.com",
).rstrip("/")
API = f"{BASE}/api"


@pytest.fixture(scope="module")
def client():
    with httpx.Client(timeout=45.0) as c:
        # ensure clean slate
        c.delete(f"{API}/growth/capabilities")
        yield c
        c.delete(f"{API}/growth/capabilities")


def test_growth_stats_includes_grown_field(client):
    r = client.get(f"{API}/growth/stats")
    assert r.status_code == 200
    body = r.json()
    assert "grown_capabilities" in body
    assert isinstance(body["grown_capabilities"], int)


def test_manual_growth_spawn(client):
    r = client.post(
        f"{API}/growth/spawn",
        json={"trigger": "manual", "hint": "harmonic pattern", "force": True},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["spawned"] is True
    cap = body["capability"]
    assert cap["slug"] and "/" not in cap["slug"]
    assert cap["name"]
    assert cap["category"] in {"memory", "perception", "lattice", "network", "meta", "chaos"}
    assert 0.0 <= cap["activation"] <= 1.0
    assert cap["trigger"] == "manual"


def test_list_capabilities_returns_spawned(client):
    r = client.get(f"{API}/growth/capabilities")
    assert r.status_code == 200
    caps = r.json()
    assert isinstance(caps, list)
    assert len(caps) >= 1


def test_execute_capability(client):
    caps = client.get(f"{API}/growth/capabilities").json()
    assert caps, "need at least one capability"
    slug = caps[0]["slug"]
    r = client.post(
        f"{API}/growth/execute",
        json={"slug": slug, "args": "test run"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["slug"] == slug
    assert body["result"]
    assert body["invocations"] >= 1


def test_autonomous_cooldown_gate(client):
    """Autonomous spawn within cooldown must return spawned=False."""
    # force first autonomous spawn
    client.post(
        f"{API}/growth/spawn",
        json={"trigger": "autonomous", "force": True},
    )
    # immediately try without force — should be gated
    r = client.post(
        f"{API}/growth/spawn",
        json={"trigger": "autonomous"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["spawned"] is False
    assert body["reason"] == "cooldown"
    assert body["cooldown_remaining"] > 0


def test_growth_log_endpoint(client):
    r = client.get(f"{API}/growth/log?limit=10")
    assert r.status_code == 200
    body = r.json()
    assert "events" in body
    assert isinstance(body["events"], list)


def test_cull_capability(client):
    caps = client.get(f"{API}/growth/capabilities").json()
    if not caps:
        client.post(
            f"{API}/growth/spawn",
            json={"trigger": "manual", "force": True},
        )
        caps = client.get(f"{API}/growth/capabilities").json()
    slug = caps[0]["slug"]
    r = client.delete(f"{API}/growth/capabilities/{slug}")
    assert r.status_code == 200
    assert r.json()["culled"] == slug
    after = client.get(f"{API}/growth/capabilities").json()
    assert all(c["slug"] != slug for c in after)


def test_404_for_unknown_capability(client):
    r = client.post(
        f"{API}/growth/execute",
        json={"slug": "does-not-exist", "args": "x"},
    )
    assert r.status_code == 404


def test_chat_and_lattice_still_work(client):
    """Regression: pre-existing endpoints must not have broken."""
    r1 = client.get(f"{API}/health")
    assert r1.status_code == 200
    r2 = client.get(f"{API}/lattice/state")
    assert r2.status_code == 200
    r3 = client.get(f"{API}/introspect")
    assert r3.status_code == 200
