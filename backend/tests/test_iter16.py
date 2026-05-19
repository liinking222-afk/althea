"""Regression: Iteration 16 — Evolution Engine (autonomous self-update).

Run with:
    cd /app/backend && python -m pytest tests/test_iter16.py -v
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
    with httpx.Client(timeout=60.0) as c:
        # reset evolution state
        c.delete(f"{API}/evolution/cycles")
        yield c
        c.delete(f"{API}/evolution/cycles")


def test_version_starts_at_1_0_0(client):
    r = client.get(f"{API}/evolution/version")
    assert r.status_code == 200
    d = r.json()
    assert d["version"] == "1.0.0"
    assert d["cycles"] == 0
    assert "LINUS" in d["archetypes"]
    assert "CARMACK" in d["archetypes"]
    assert len(d["archetypes"]) == 11


def test_archetypes_endpoint(client):
    r = client.get(f"{API}/evolution/archetypes")
    assert r.status_code == 200
    data = r.json()
    assert any(a["key"] == "LINUS" for a in data)
    assert all("doctrine" in a for a in data)


def test_manual_tick_force(client):
    r = client.post(
        f"{API}/evolution/tick",
        json={"trigger": "manual", "force": True, "archetype": "CARMACK"},
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["evolved"] is True
    c = d["cycle"]
    assert c["cycle_number"] == 1
    assert c["archetype"] == "CARMACK"
    assert c["version_before"] == "1.0.0"
    assert c["version_after"] == "1.0.1"
    assert c["node_id"].startswith("EVO-")
    assert c["applied"] is True


def test_version_bumps_after_tick(client):
    r = client.get(f"{API}/evolution/version")
    assert r.json()["version"] == "1.0.1"


def test_self_archetype_bumps_minor(client):
    r = client.post(
        f"{API}/evolution/tick",
        json={"trigger": "manual", "force": True, "archetype": "SELF"},
    )
    assert r.status_code == 200
    c = r.json()["cycle"]
    assert c["archetype"] == "SELF"
    # 1.0.1 -> 1.1.0
    assert c["version_after"] == "1.1.0"


def test_autonomous_cooldown(client):
    # First autonomous tick
    r1 = client.post(f"{API}/evolution/tick", json={"trigger": "autonomous", "force": True})
    assert r1.status_code == 200
    assert r1.json()["evolved"] is True
    # Immediate second — gated
    r2 = client.post(f"{API}/evolution/tick", json={"trigger": "autonomous"})
    d2 = r2.json()
    assert d2["evolved"] is False
    assert d2["reason"] == "cooldown"
    assert d2["cooldown_remaining"] > 0


def test_master_update_endpoint(client):
    r = client.post(
        f"{API}/evolution/master-update",
        json={"archetype": "DIJKSTRA"},
    )
    assert r.status_code == 200
    d = r.json()
    assert d["evolved"] is True
    assert d["cycle"]["archetype"] == "DIJKSTRA"
    assert d["cycle"]["trigger"] == "master"


def test_unknown_archetype_master(client):
    r = client.post(
        f"{API}/evolution/master-update",
        json={"archetype": "FAKEDUDE"},
    )
    assert r.status_code == 400


def test_cycles_list(client):
    r = client.get(f"{API}/evolution/cycles")
    assert r.status_code == 200
    cycles = r.json()
    assert len(cycles) >= 3
    # Cycles sorted desc
    nums = [c["cycle_number"] for c in cycles]
    assert nums == sorted(nums, reverse=True)


def test_evo_node_appears_in_lattice(client):
    """EVO-XXXX nodes must exist in the lattice with is_evolution=True."""
    r = client.get(f"{API}/lattice/nodes")
    assert r.status_code == 200
    nodes = r.json()
    evo_nodes = [n for n in nodes if n["id"].startswith("EVO-")]
    assert len(evo_nodes) >= 1
    assert any(n.get("is_evolution") for n in evo_nodes)
    assert any(n.get("archetype") for n in evo_nodes)


def test_evolution_emits_notification(client):
    r = client.get(f"{API}/notifications?category=growth&limit=50")
    assert r.status_code == 200
    notifs = r.json()
    evo_notifs = [
        n for n in notifs
        if n.get("payload", {}).get("cycle_number") is not None
    ]
    assert len(evo_notifs) >= 1


def test_growth_stats_includes_evolution_cycles(client):
    r = client.get(f"{API}/growth/stats")
    assert r.status_code == 200
    d = r.json()
    assert "evolution_cycles" in d
    assert d["evolution_cycles"] >= 1


def test_reset_cycles(client):
    r = client.delete(f"{API}/evolution/cycles")
    assert r.status_code == 200
    assert r.json()["reset"] is True
    v = client.get(f"{API}/evolution/version").json()
    assert v["version"] == "1.0.0"
    assert v["cycles"] == 0
