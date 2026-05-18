"""Iter13 backend tests: Wi-Fi network profile manifest endpoints + network graph integration."""
import os
import time
import requests
import pytest
from pathlib import Path

# Load REACT_APP_BACKEND_URL from frontend/.env if not in env
_env_path = Path("/app/frontend/.env")
if not os.environ.get("REACT_APP_BACKEND_URL") and _env_path.exists():
    for line in _env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            os.environ["REACT_APP_BACKEND_URL"] = line.split("=", 1)[1].strip().strip('"')
            break

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Health ----------
def test_health(client):
    r = client.get(f"{API}/")
    assert r.status_code in (200, 404)  # router root may not exist; just sanity


# ---------- Empty SSID -> 400 ----------
def test_create_profile_empty_ssid(client):
    r = client.post(f"{API}/network/profile", json={"ssid": ""})
    assert r.status_code == 400, r.text


# ---------- Create profile + has_password=true ----------
def test_create_profile_with_password(client):
    payload = {
        "ssid": "TEST_Althea-Lab",
        "security": "wpa3",  # lower-case -> backend should uppercase
        "password": "sovereign",
        "label": "iter13-secured",
    }
    r = client.post(f"{API}/network/profile", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ssid"] == "TEST_Althea-Lab"
    assert data["security"] == "WPA3"  # uppercased
    assert data["label"] == "iter13-secured"
    assert data["has_password"] is True
    assert "id" in data and isinstance(data["id"], str)
    # password / password_hash must never be returned
    assert "password" not in data
    assert "password_hash" not in data


# ---------- Create profile without password ----------
def test_create_profile_open(client):
    payload = {"ssid": "TEST_OpenLab", "security": "OPEN"}
    r = client.post(f"{API}/network/profile", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ssid"] == "TEST_OpenLab"
    assert data["security"] == "OPEN"
    assert data["has_password"] is False


# ---------- GET /network/profiles ----------
def test_list_profiles(client):
    r = client.get(f"{API}/network/profiles")
    assert r.status_code == 200, r.text
    arr = r.json()
    assert isinstance(arr, list)
    ssids = [p["ssid"] for p in arr]
    assert "TEST_Althea-Lab" in ssids
    assert "TEST_OpenLab" in ssids
    # password fields must not leak
    for p in arr:
        assert "password" not in p
        assert "password_hash" not in p
    # most-recent-first: timestamps non-increasing
    timestamps = [p.get("timestamp") for p in arr if p.get("timestamp")]
    assert timestamps == sorted(timestamps, reverse=True)


# ---------- network/graph picks up wifi peripheral ----------
def test_graph_contains_wifi_peripheral(client):
    r = client.get(f"{API}/network/graph")
    assert r.status_code == 200, r.text
    g = r.json()
    labels = [n["label"] for n in g["nodes"] if n["type"] == "peripheral"]
    # peripheral label should start with WIFI:<first 16 chars of ssid>
    assert any(lbl.startswith("WIFI:TEST_Althea-La") or lbl.startswith("WIFI:TEST_Althea") for lbl in labels), labels


# ---------- Memory tagged wifi/profile/<sec_lower> ----------
def test_memory_logged_for_profile(client):
    r = client.get(f"{API}/memory?limit=100")
    assert r.status_code == 200, r.text
    body = r.json()
    mems = body if isinstance(body, list) else body.get("memories", [])
    matched = [m for m in mems if "[NETWORK-PROFILE]" in (m.get("content") or "")]
    assert matched, "no NETWORK-PROFILE memory found"
    tags_union = set()
    for m in matched:
        tags_union.update(m.get("tags") or [])
    assert "wifi" in tags_union
    assert "profile" in tags_union
    # WPA3 or open security tag should be present
    assert ("wpa3" in tags_union) or ("open" in tags_union)


# ---------- DELETE profile removes profile + peripheral ----------
def test_delete_profile(client):
    # create a fresh one
    r = client.post(f"{API}/network/profile", json={"ssid": "TEST_DeleteMe", "security": "WPA2"})
    assert r.status_code == 200
    pid = r.json()["id"]
    # delete
    r = client.delete(f"{API}/network/profile/{pid}")
    assert r.status_code == 200, r.text
    assert r.json().get("deleted") == pid
    # verify gone in list
    r = client.get(f"{API}/network/profiles")
    assert pid not in [p["id"] for p in r.json()]
    # verify peripheral_link removed from graph
    time.sleep(0.3)
    g = client.get(f"{API}/network/graph").json()
    p_labels = [n["label"] for n in g["nodes"] if n["type"] == "peripheral"]
    assert not any(lbl.startswith("WIFI:TEST_DeleteMe") for lbl in p_labels), p_labels
    # deleting non-existent -> 404
    r = client.delete(f"{API}/network/profile/not-an-id-xyz")
    assert r.status_code == 404


# ---------- Cleanup remaining TEST_ profiles ----------
def test_zz_cleanup(client):
    r = client.get(f"{API}/network/profiles")
    for p in r.json():
        if p.get("ssid", "").startswith("TEST_"):
            client.delete(f"{API}/network/profile/{p['id']}")


# ---------- Regression: bridge/web still works ----------
def test_regression_bridge_web(client):
    r = client.post(f"{API}/bridge/web", json={"url": "https://example.com"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["host"] == "example.com"
    assert data["status"] in (200, 301, 302)
    assert "memory_id" in data


# ---------- Regression: introspect still works ----------
def test_regression_introspect(client):
    r = client.get(f"{API}/introspect")
    assert r.status_code == 200, r.text
    j = r.json()
    assert "integrity" in j


# ---------- Regression: /spawn-equivalent lattice/node still works ----------
def test_regression_lattice_node_create(client):
    r = client.post(f"{API}/lattice/nodes", json={"context": "TEST_iter13_thought"})
    assert r.status_code == 200, r.text
    assert "id" in r.json()
