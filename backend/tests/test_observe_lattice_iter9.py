"""Iteration 9: /api/observe spawns lattice nodes + reflection memories."""
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
    # baseline wipe
    s.delete(f"{API}/lattice/nodes", timeout=15)
    s.delete(f"{API}/memory", timeout=15)
    return s


def test_observe_watch_spawns_node_and_reflection(session):
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    r = session.post(f"{API}/observe", json={"url": url, "action": "watch"}, timeout=60)
    assert r.status_code == 200, r.text
    d = r.json()
    # response shape unchanged
    for k in ("url", "title", "interpretation", "memory_id", "timestamp"):
        assert k in d
    assert d["url"] == url
    assert d["memory_id"]

    # Verify node created with NODE-0000
    nodes = session.get(f"{API}/lattice/nodes", timeout=15).json()
    assert len(nodes) == 1
    assert re.match(r"^NODE-\d{4}$", nodes[0]["id"])
    assert nodes[0]["id"] == "NODE-0000"
    # memory_trace begins with [OBSERVATION:
    assert nodes[0]["memory_trace"].startswith("[OBSERVATION:")

    # Verify reflection memory exists with required tags incl youtube
    mems = session.get(f"{API}/memory", timeout=15).json()
    reflections = [m for m in mems if "reflection" in m.get("tags", [])]
    assert len(reflections) >= 1
    r0 = reflections[0]
    for t in ("reflection", "learn", "observation"):
        assert t in r0["tags"], f"missing tag {t}: {r0['tags']}"
    # youtube tag for YouTube URL
    assert "youtube" in r0["tags"]
    assert r0["source"] == "lattice"


def test_observe_second_watch_sequential_node_id(session):
    url2 = "https://en.wikipedia.org/wiki/Recursion"
    r = session.post(f"{API}/observe", json={"url": url2, "action": "watch"}, timeout=60)
    assert r.status_code == 200, r.text
    nodes = session.get(f"{API}/lattice/nodes", timeout=15).json()
    ids = sorted([n["id"] for n in nodes])
    assert ids == ["NODE-0000", "NODE-0001"]

    # Verify a 2nd reflection memory
    mems = session.get(f"{API}/memory", timeout=15).json()
    reflections = [m for m in mems if "reflection" in m.get("tags", [])]
    assert len(reflections) >= 2
    # Non-youtube URL must NOT have youtube tag
    non_yt = [m for m in reflections if "youtube" not in m.get("tags", [])]
    assert len(non_yt) >= 1


def test_observe_stop_does_not_spawn_node(session):
    # snapshot
    nodes_before = session.get(f"{API}/lattice/nodes", timeout=15).json()
    refl_before = [m for m in session.get(f"{API}/memory", timeout=15).json()
                   if "reflection" in m.get("tags", [])]

    r = session.post(f"{API}/observe", json={"url": "", "action": "stop"}, timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["memory_id"]

    nodes_after = session.get(f"{API}/lattice/nodes", timeout=15).json()
    refl_after = [m for m in session.get(f"{API}/memory", timeout=15).json()
                  if "reflection" in m.get("tags", [])]
    assert len(nodes_after) == len(nodes_before), "stop must not spawn lattice node"
    assert len(refl_after) == len(refl_before), "stop must not create reflection memory"


def test_observe_empty_url_watch_no_spawn(session):
    nodes_before = session.get(f"{API}/lattice/nodes", timeout=15).json()
    r = session.post(f"{API}/observe", json={"url": "", "action": "watch"}, timeout=15)
    assert r.status_code == 200
    nodes_after = session.get(f"{API}/lattice/nodes", timeout=15).json()
    assert len(nodes_after) == len(nodes_before), "empty url must not spawn lattice node"


def test_observe_response_shape_unchanged(session):
    r = session.post(
        f"{API}/observe",
        json={"url": "https://en.wikipedia.org/wiki/Lattice", "action": "watch"},
        timeout=60,
    )
    assert r.status_code == 200
    d = r.json()
    # exactly the 5 documented keys (or superset only if explicitly allowed)
    expected = {"url", "title", "interpretation", "memory_id", "timestamp"}
    assert expected.issubset(set(d.keys()))
    # ensure no node_id leaked into response
    assert "node_id" not in d
    assert "_id" not in d
