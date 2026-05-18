"""Regression: Iteration 15 — Cyberpunk Terminal, Browser, Server, Code,
Satellite, Notifications, Files, Desktop Download, Neural Zoom.

Run with:
    cd /app/backend && python -m pytest tests/test_iter15.py -v
"""
import io
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
        # clean slate
        c.delete(f"{API}/notifications")
        yield c


def test_notifications_empty_then_push(client):
    r = client.get(f"{API}/notifications/count")
    assert r.status_code == 200
    base = r.json()["total"]

    r = client.post(
        f"{API}/notifications",
        json={"title": "test ping", "body": "hi", "category": "system"},
    )
    assert r.status_code == 200
    n = r.json()
    assert n["title"] == "test ping"
    assert n["seen"] is False

    r = client.get(f"{API}/notifications/count")
    assert r.json()["total"] == base + 1


def test_notification_mark_seen(client):
    r = client.post(f"{API}/notifications", json={"title": "x"})
    nid = r.json()["id"]
    r = client.post(f"{API}/notifications/{nid}/seen")
    assert r.status_code == 200
    r = client.get(f"{API}/notifications?limit=200")
    target = next(x for x in r.json() if x["id"] == nid)
    assert target["seen"] is True


def test_file_upload_text(client):
    files = {"file": ("hello.txt", b"hello althea\n", "text/plain")}
    r = client.post(f"{API}/files/upload", files=files)
    assert r.status_code == 200
    d = r.json()
    assert d["filename"] == "hello.txt"
    assert d["is_text"] is True
    assert d["text_preview"].startswith("hello althea")

    # list shows it
    r2 = client.get(f"{API}/files")
    assert any(f["id"] == d["id"] for f in r2.json())

    # download returns same content
    r3 = client.get(f"{API}/files/{d['id']}/download")
    assert r3.status_code == 200
    assert r3.content == b"hello althea\n"

    # cleanup
    client.delete(f"{API}/files/{d['id']}")


def test_file_too_large(client):
    big = b"x" * (3 * 1024 * 1024)
    files = {"file": ("big.bin", big, "application/octet-stream")}
    r = client.post(f"{API}/files/upload", files=files)
    assert r.status_code == 413


def test_browser_fetch_real_url(client):
    r = client.post(f"{API}/browser/fetch", json={"url": "https://example.com"})
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == 200
    assert d["title"] == "Example Domain"
    assert "Example Domain" in d["text"]
    assert len(d["links"]) >= 1


def test_browser_fetch_invalid_host(client):
    r = client.post(f"{API}/browser/fetch", json={"url": "https://nonexistent-althea-xyz12345.test"})
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == 0
    assert d.get("error")


def test_server_diagnose_http(client):
    r = client.post(
        f"{API}/server/diagnose",
        json={"host": "1.1.1.1", "protocol": "https"},
    )
    assert r.status_code == 200
    d = r.json()
    assert d["host"] == "1.1.1.1"
    assert d["status"] in ("REACHABLE", "UNREACHABLE")
    assert d["details"]["tcp_ok"] in (True, False)


def test_server_diagnose_ssh_gated(client):
    r = client.post(
        f"{API}/server/diagnose",
        json={"host": "github.com", "protocol": "ssh"},
    )
    assert r.status_code == 200
    d = r.json()
    # github.com:22 is reachable but should be GATED for non-http
    assert d["status"] in ("GATED", "UNREACHABLE")


def test_satellite_feed(client):
    r = client.get(f"{API}/satellite/feed")
    assert r.status_code == 200
    d = r.json()
    assert len(d["satellites"]) > 20
    assert d["metrics"]["total"] == len(d["satellites"])
    assert 0 <= d["metrics"]["avg_signal"] <= 1


def test_code_generate_and_apply(client):
    r = client.post(
        f"{API}/code/generate",
        json={"intent": "print hello world", "language": "python"},
    )
    assert r.status_code == 200
    d = r.json()
    assert d["language"] == "python"
    assert d["intent"] == "print hello world"
    assert len(d["code"]) > 0

    # apply
    r2 = client.post(f"{API}/code/apply", json={"id": d["id"]})
    assert r2.status_code == 200
    a = r2.json()
    assert a["applied"] is True
    assert a["path"].endswith(".py")

    # list shows it
    r3 = client.get(f"{API}/code")
    assert any(x["id"] == d["id"] for x in r3.json())

    # cleanup
    client.delete(f"{API}/code/{d['id']}")


def test_desktop_download(client):
    r = client.get(f"{API}/desktop/download")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/gzip"
    assert "althea-desktop" in r.headers.get("content-disposition", "")
    assert len(r.content) > 1000  # actual tarball


def test_desktop_manifest(client):
    r = client.get(f"{API}/desktop/manifest")
    assert r.status_code == 200
    d = r.json()
    assert d["port"] == 7788
    assert "althea.sh" in d["files"]


def test_growth_routes_to_notification(client):
    """Growth spawns should now emit a notification with category=growth."""
    before = client.get(f"{API}/notifications?category=growth").json()
    before_count = len(before)
    r = client.post(
        f"{API}/growth/spawn",
        json={"trigger": "manual", "force": True, "hint": "iter15 probe"},
    )
    assert r.status_code == 200
    assert r.json()["spawned"] is True
    slug = r.json()["capability"]["slug"]
    after = client.get(f"{API}/notifications?category=growth").json()
    assert len(after) >= before_count + 1
    # latest notification mentions the slug
    assert any(slug in (n["payload"] or {}).get("slug", "") for n in after)
    # cleanup
    client.delete(f"{API}/growth/capabilities/{slug}")


def test_regression_baseline(client):
    """Make sure prior endpoints still respond 200."""
    for path in [
        "/health", "/lattice/state", "/introspect",
        "/memory", "/growth/stats", "/cognition/threads",
    ]:
        r = client.get(f"{API}{path}")
        assert r.status_code == 200, f"{path} broke"
