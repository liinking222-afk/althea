"""Iteration 10: Web Bridge + Network Graph tests."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback to local
    BASE_URL = "http://localhost:8001"
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Web Bridge ----------
class TestWebBridge:
    def test_bridge_empty_url_400(self, session):
        r = session.post(f"{API}/bridge/web", json={"url": ""})
        assert r.status_code == 400, r.text

    def test_bridge_example_com_real_fetch(self, session):
        r = session.post(f"{API}/bridge/web", json={"url": "example.com"}, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # Required keys
        for k in [
            "url", "host", "status", "title", "description", "text_excerpt",
            "links", "elapsed_ms", "memory_id", "timestamp",
        ]:
            assert k in data, f"missing key {k}"
        # https prefix applied
        assert data["url"].startswith("https://"), data["url"]
        assert data["host"] == "example.com"
        assert data["status"] == 200
        assert data["title"] == "Example Domain"
        assert isinstance(data["links"], list)
        assert isinstance(data["elapsed_ms"], int)
        assert data["memory_id"]

    def test_bridge_writes_memory_with_host_tag(self, session):
        # trigger a fresh fetch
        r = session.post(f"{API}/bridge/web", json={"url": "https://example.com"}, timeout=30)
        assert r.status_code == 200
        memory_id = r.json()["memory_id"]

        # Read memories — should contain the new bridge memory
        rm = session.get(f"{API}/memory")
        assert rm.status_code == 200
        mems = rm.json()
        match = [m for m in mems if m.get("id") == memory_id]
        assert match, "bridge memory not persisted"
        mem = match[0]
        tags = mem.get("tags", [])
        assert "bridge" in tags
        assert "web" in tags
        assert "example.com" in tags

    def test_bridge_invalid_host_502(self, session):
        r = session.post(
            f"{API}/bridge/web",
            json={"url": "http://this-domain-should-not-exist-althea-xyz-987654.invalid"},
            timeout=30,
        )
        assert r.status_code == 502, r.text


# ---------- Network Graph ----------
class TestNetworkGraph:
    def test_graph_basic_shape(self, session):
        r = session.get(f"{API}/network/graph")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "nodes" in data and "edges" in data and "generated_at" in data
        assert isinstance(data["nodes"], list) and isinstance(data["edges"], list)
        # Always at least the core
        core = [n for n in data["nodes"] if n["type"] == "core" and n["id"] == "althea"]
        assert core, "althea core node missing"
        assert core[0]["label"] == "ALTHEA"

    def test_graph_after_seeding(self, session):
        # 1) grant OPTIC peripheral via lattice perception
        rp = session.post(
            f"{API}/lattice/perception",
            json={
                "modality": "OPTIC",
                "endpoint": "https://example.com/feed",
                "status": "LISTENING",
            },
        )
        assert rp.status_code == 200, rp.text

        # 2) spawn 2 lattice nodes
        for _ in range(2):
            rs = session.post(
                f"{API}/lattice/nodes",
                json={"context": "iter10 graph test"},
            )
            assert rs.status_code == 200, rs.text

        # 3) bridge example.com
        rb = session.post(f"{API}/bridge/web", json={"url": "example.com"}, timeout=30)
        assert rb.status_code == 200, rb.text

        # let backend settle
        time.sleep(0.5)

        rg = session.get(f"{API}/network/graph")
        assert rg.status_code == 200
        g = rg.json()
        types = {n["type"] for n in g["nodes"]}
        assert "core" in types
        assert "peripheral" in types
        assert "cognitive" in types
        assert "host" in types, f"types found: {types}"

        # at least 2 cognitive nodes
        cog = [n for n in g["nodes"] if n["type"] == "cognitive"]
        assert len(cog) >= 2, f"only {len(cog)} cognitive nodes"

        # example.com host
        hosts = [n for n in g["nodes"] if n["type"] == "host"]
        host_labels = {n["label"] for n in hosts}
        assert "example.com" in host_labels, host_labels

        # edge kinds present
        kinds = {e["kind"] for e in g["edges"]}
        assert "perceives" in kinds
        assert "spawned" in kinds
        assert "observed" in kinds or "parent" in kinds, f"kinds: {kinds}"


# ---------- Regression: prior endpoints still alive ----------
class TestRegression:
    def test_memory_list(self, session):
        r = session.get(f"{API}/memory")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_observe_endpoint_alive(self, session):
        # POST /observe with minimal body
        r = session.post(
            f"{API}/observe",
            json={"url": "https://example.com", "note": "iter10-regression"},
        )
        # 200 expected
        assert r.status_code in (200, 201), r.text
