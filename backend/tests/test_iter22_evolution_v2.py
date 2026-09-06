"""Iteration 22 — Evolution Engine AEE/2.0 (self-directed growth protocol) regression."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"
VECTORS = ["PERCEPTION", "MEMORY", "REASONING", "SYNTHESIS",
           "AUTONOMY", "EFFICIENCY", "CREATIVITY", "RESILIENCE"]


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


def test_version_reports_protocol(s):
    j = s.get(f"{API}/evolution/version", timeout=15).json()
    assert j["protocol"] == "AEE/2.0"
    assert j["vectors"] == VECTORS
    assert "verified_upgrades" in j


def test_assessment_shape_and_weights(s):
    j = s.get(f"{API}/evolution/assessment", timeout=30).json()
    rows = j["vectors"]
    assert {r["vector"] for r in rows} == set(VECTORS)
    assert abs(sum(r["probability"] for r in rows) - 1.0) < 1e-3
    assert j["favored"] == rows[0]["vector"]
    for r in rows:
        assert 0 <= r["pressure"] <= 1 and r["reason"]


@pytest.mark.parametrize("vector", VECTORS)
def test_forced_vector_forges_verified_module(s, vector):
    r = s.post(f"{API}/evolution/tick", json={"trigger": "manual", "force": True, "vector": vector}, timeout=60)
    assert r.status_code == 200
    j = r.json()
    assert j["evolved"] and j["target"] == vector
    assert j["verified"] is True, j["cycle"]["verification"]
    assert j["cycle"]["vector"] == vector and j["cycle"]["forced"] is True
    assert j["node_id"].startswith("EVO-")
    pytest.last_upgrade = j["upgrade_id"]


def test_upgrade_registry_and_runtime_invoke(s):
    ups = s.get(f"{API}/evolution/upgrades?vector=AUTONOMY&limit=1", timeout=15).json()
    assert ups and ups[0]["module"] == "direct_cognition_v2" and ups[0]["verified"]
    r = s.post(f"{API}/evolution/upgrades/{ups[0]['upgrade_id']}/run",
               json={"args": ["convert 10 km to miles"]}, timeout=30).json()
    assert r["result"]["route"] == "local" and "6.21371" in r["result"]["answer"]


def test_run_unknown_upgrade_404(s):
    assert s.post(f"{API}/evolution/upgrades/deadbeef/run", json={}, timeout=15).status_code == 404


def test_chat_zero_llm_direct_cognition_v2(s):
    r = s.post(f"{API}/chat", json={"message": "what is 17 * 23 + 5?", "session_id": "iter22-evo"}, timeout=60).json()
    assert "EVO-V2" in r["tags"] and "ZERO-LLM" in r["tags"]
    assert "= 396" in r["reply"]


def test_cycles_carry_v2_fields(s):
    c = s.get(f"{API}/evolution/cycles?limit=3", timeout=15).json()
    assert c and c[0]["vector"] in VECTORS and c[0]["module"] and c[0]["upgrade_id"]
    assert abs(sum(c[0]["weights"].values()) - 1.0) < 1e-2


def test_master_update_lens(s):
    j = s.post(f"{API}/evolution/master-update", json={"archetype": "DIJKSTRA", "vector": "REASONING"}, timeout=60).json()
    assert j["evolved"] and j["cycle"]["archetype"] == "DIJKSTRA" and j["target"] == "REASONING"
