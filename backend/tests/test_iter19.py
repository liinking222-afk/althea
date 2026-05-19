"""Regression: Iteration 19 — Wi-Fi export + Bluetooth/USB lattice/learn.

Run with:
    cd /app/backend && python -m pytest tests/test_iter19.py -v
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
    with httpx.Client(timeout=30.0) as c:
        yield c


@pytest.fixture
def profile_id(client):
    r = client.post(
        f"{API}/network/profile",
        json={
            "ssid": "AlthEa-Test-Net",
            "security": "WPA2",
            "password": "hunter2-xyz",
            "label": "iter19-test",
        },
    )
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    yield pid
    client.delete(f"{API}/network/profile/{pid}")


def test_export_mobileconfig(client, profile_id):
    r = client.post(
        f"{API}/network/profile/{profile_id}/export?fmt=mobileconfig",
        json={"password": "hunter2-xyz"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/x-apple-aspen-config"
    assert ".mobileconfig" in r.headers.get("content-disposition", "")
    body = r.text
    assert "<?xml version" in body
    assert "AlthEa-Test-Net" in body
    assert "hunter2-xyz" in body
    assert "<key>SSID_STR</key>" in body
    assert "com.apple.wifi.managed" in body
    assert "<key>EncryptionType</key>" in body


def test_export_mobileconfig_placeholder_when_no_password(client, profile_id):
    r = client.post(
        f"{API}/network/profile/{profile_id}/export?fmt=mobileconfig",
        json={"password": None},
    )
    assert r.status_code == 200
    assert "REPLACE_WITH_YOUR_PASSWORD" in r.text


def test_export_wpa_supplicant(client, profile_id):
    r = client.post(
        f"{API}/network/profile/{profile_id}/export?fmt=wpa_supplicant",
        json={"password": "hunter2-xyz"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    body = r.text
    assert 'ssid="AlthEa-Test-Net"' in body
    assert 'psk="hunter2-xyz"' in body
    assert "key_mgmt=WPA-PSK" in body


def test_export_wpa3_uses_sae(client):
    r = client.post(
        f"{API}/network/profile",
        json={
            "ssid": "wpa3-net",
            "security": "WPA3",
            "password": "supersecure",
            "label": "wpa3",
        },
    )
    pid = r.json()["id"]
    try:
        r2 = client.post(
            f"{API}/network/profile/{pid}/export?fmt=wpa_supplicant",
            json={"password": "supersecure"},
        )
        assert r2.status_code == 200
        assert "key_mgmt=SAE" in r2.text
        assert "ieee80211w=2" in r2.text
    finally:
        client.delete(f"{API}/network/profile/{pid}")


def test_export_open_network(client):
    r = client.post(
        f"{API}/network/profile",
        json={"ssid": "open-net", "security": "OPEN", "label": "lobby"},
    )
    pid = r.json()["id"]
    try:
        r2 = client.post(
            f"{API}/network/profile/{pid}/export?fmt=wpa_supplicant",
            json={"password": None},
        )
        assert r2.status_code == 200
        assert "key_mgmt=NONE" in r2.text
        assert "psk=" not in r2.text
    finally:
        client.delete(f"{API}/network/profile/{pid}")


def test_export_unknown_format(client, profile_id):
    r = client.post(
        f"{API}/network/profile/{profile_id}/export?fmt=zigzag",
        json={"password": "x"},
    )
    assert r.status_code == 400


def test_export_unknown_profile(client):
    r = client.post(
        f"{API}/network/profile/does-not-exist/export?fmt=mobileconfig",
        json={"password": "x"},
    )
    assert r.status_code == 404


def test_lattice_learn_still_works(client):
    """Sanity: the endpoint the frontend now hits for every pairing exists."""
    r = client.post(
        f"{API}/lattice/learn",
        json={
            "stream": "[USB-PAIRED iter19-probe] endpoint=usb:probe at=2026",
            "label": "pairing:usb",
        },
    )
    assert r.status_code == 200
    d = r.json()
    assert d["node_id"]
    assert d["pattern"]
