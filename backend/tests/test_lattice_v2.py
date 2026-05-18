"""ALTHEA v2 Self-Extension Module (iter 8) lattice tests."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    # Wipe lattice nodes baseline
    s.delete(f"{API}/lattice/nodes", timeout=15)
    return s


# -------- Cognitive Nodes --------
def test_spawn_node_id_format(session):
    r = session.post(f"{API}/lattice/nodes", json={"context": "TEST_node alpha"}, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert re.match(r"^NODE-\d{4}$", d["id"]), f"bad id: {d['id']}"
    assert d["activation"] == 1.0
    assert d["parent_id"] is None
    assert "alpha" in d["memory_trace"]
    assert "_id" not in d


def test_spawn_node_empty_context_400(session):
    r = session.post(f"{API}/lattice/nodes", json={"context": "   "}, timeout=15)
    assert r.status_code == 400


def test_spawn_node_parent_not_found_404(session):
    r = session.post(f"{API}/lattice/nodes", json={"context": "ctx", "parent_id": "NODE-9999"}, timeout=15)
    assert r.status_code == 404


def test_spawn_node_with_parent_ok(session):
    p = session.post(f"{API}/lattice/nodes", json={"context": "parent"}, timeout=15).json()
    c = session.post(f"{API}/lattice/nodes", json={"context": "child", "parent_id": p["id"]}, timeout=15)
    assert c.status_code == 200
    assert c.json()["parent_id"] == p["id"]


def test_list_nodes_sorted_asc_no_id(session):
    r = session.get(f"{API}/lattice/nodes", timeout=15)
    assert r.status_code == 200
    arr = r.json()
    assert isinstance(arr, list) and len(arr) >= 3
    ts = [n["timestamp"] for n in arr]
    assert ts == sorted(ts), "nodes not sorted asc by timestamp"
    for n in arr:
        assert "_id" not in n
        assert re.match(r"^NODE-\d{4}$", n["id"])


def test_delete_all_nodes(session):
    r = session.delete(f"{API}/lattice/nodes", timeout=15)
    assert r.status_code == 200
    assert "deleted" in r.json()
    assert session.get(f"{API}/lattice/nodes", timeout=15).json() == []


# -------- Perception --------
def test_perception_upsert_uppercase(session):
    # cleanup
    for m in ["OPTIC", "AUDIO", "GPS"]:
        session.delete(f"{API}/lattice/perception/{m}", timeout=15)
    r = session.post(f"{API}/lattice/perception", json={"modality": "optic", "endpoint": "cam-A"}, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["modality"] == "OPTIC"
    assert d["endpoint"] == "cam-A"
    assert d["status"] == "LISTENING"

    # Upsert: same modality should overwrite endpoint not duplicate
    r2 = session.post(f"{API}/lattice/perception", json={"modality": "OPTIC", "endpoint": "cam-B"}, timeout=15)
    assert r2.status_code == 200
    lst = session.get(f"{API}/lattice/perception", timeout=15).json()
    optics = [x for x in lst if x["modality"] == "OPTIC"]
    assert len(optics) == 1
    assert optics[0]["endpoint"] == "cam-B"


def test_perception_list_no_id(session):
    lst = session.get(f"{API}/lattice/perception", timeout=15).json()
    assert isinstance(lst, list)
    for x in lst:
        assert "_id" not in x


def test_perception_delete_and_404(session):
    session.post(f"{API}/lattice/perception", json={"modality": "USB", "endpoint": "usb-x"}, timeout=15)
    r = session.delete(f"{API}/lattice/perception/USB", timeout=15)
    assert r.status_code == 200
    r2 = session.delete(f"{API}/lattice/perception/USB", timeout=15)
    assert r2.status_code == 404


# -------- Autonomous Learn --------
def test_learn_empty_stream_400(session):
    r = session.post(f"{API}/lattice/learn", json={"stream": "   "}, timeout=15)
    assert r.status_code == 400


def test_learn_spawns_node_and_memory(session):
    # Wipe to deterministic
    session.delete(f"{API}/lattice/nodes", timeout=15)
    before_mem = session.get(f"{API}/memory", timeout=15).json()
    r = session.post(
        f"{API}/lattice/learn",
        json={"stream": "the cat moved left then right then up", "label": "TEST_obs"},
        timeout=120,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert re.match(r"^NODE-\d{4}$", d["node_id"])
    assert d["label"] == "TEST_obs"
    assert d["pattern"] and isinstance(d["pattern"], str)
    assert d["memory_id"]

    # Verify node spawned
    nodes = session.get(f"{API}/lattice/nodes", timeout=15).json()
    assert any(n["id"] == d["node_id"] for n in nodes)

    # Verify memory created and tagged reflection+learn
    mem = session.get(f"{API}/memory", timeout=15).json()
    assert len(mem) >= len(before_mem) + 1
    target = next((m for m in mem if m["id"] == d["memory_id"]), None)
    assert target is not None
    assert "reflection" in target["tags"]
    assert "learn" in target["tags"]


# -------- Lattice State --------
def test_lattice_state_structure(session):
    r = session.get(f"{API}/lattice/state", timeout=15)
    assert r.status_code == 200, r.text
    s = r.json()
    for k in ("total_nodes", "active_links", "awareness_depth", "recent_reflections", "lattice_map"):
        assert k in s
    assert s["awareness_depth"] == s["total_nodes"]
    assert isinstance(s["recent_reflections"], list)
    assert len(s["recent_reflections"]) <= 5
    assert isinstance(s["lattice_map"], dict)
    # node id keys NODE-XXXX with float activations
    for k, v in s["lattice_map"].items():
        assert re.match(r"^NODE-\d{4}$", k)
        assert isinstance(v, (int, float))
    # reflections must be tagged 'reflection' (we verify via shape — content exists)
    for ref in s["recent_reflections"]:
        assert "content" in ref and "id" in ref


# -------- Bridge (security stub) --------
def test_bridge_empty_target_400(session):
    r = session.post(f"{API}/lattice/bridge", json={"target_ip": "  "}, timeout=15)
    assert r.status_code == 400


def test_bridge_standby_exact_message(session):
    r = session.post(f"{API}/lattice/bridge", json={"target_ip": "10.0.0.5", "protocol": "ssh"}, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["status"] == "STANDBY"
    assert d["protocol"] == "SSH"  # upper-cased
    assert d["target_ip"] == "10.0.0.5"
    assert d["message"] == "STANDBY — requires operator cryptographic approval. No connection attempted."
    assert d["memory_id"]
    # Verify memory persisted with bridge+security tags
    mem = session.get(f"{API}/memory", timeout=15).json()
    found = next((m for m in mem if m["id"] == d["memory_id"]), None)
    assert found is not None
    for t in ("bridge", "security", "ssh"):
        assert t in found["tags"]
