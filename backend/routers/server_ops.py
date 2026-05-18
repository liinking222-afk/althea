"""Server Diagnose / Connect — Althea probes any host, reports reachability.

- HTTP/HTTPS: real httpx HEAD probe with latency.
- DNS: resolve hostname.
- TCP: open a socket to host:port to check reachability.
- SSH/FTP/etc: TCP probe only; never actually executes credentials.
- Persists known servers so the operator can re-query.
"""
import asyncio
import socket
import time
from datetime import datetime, timezone
from typing import List

import httpx
from fastapi import APIRouter, HTTPException

from core import db
from models import Memory, ServerConnection, ServerProbeRequest
from routers.notifications import emit_notification

router = APIRouter()

DEFAULT_PORTS = {
    "http": 80, "https": 443, "ssh": 22, "ftp": 21,
    "redis": 6379, "postgres": 5432, "mongo": 27017,
    "mysql": 3306, "smtp": 25, "imap": 143,
}


def _tcp_probe(host: str, port: int, timeout: float = 3.0):
    """Return (reachable, latency_ms, err)."""
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, (time.perf_counter() - start) * 1000, None
    except (socket.gaierror, OSError) as e:
        return False, None, str(e)[:140]


async def _http_probe(scheme: str, host: str, port: int, timeout: float = 8.0):
    url = f"{scheme}://{host}{':' + str(port) if port not in (80, 443) else ''}"
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as cx:
            r = await cx.head(url)
            return True, (time.perf_counter() - start) * 1000, {
                "status": r.status_code,
                "server": r.headers.get("server"),
                "url": str(r.url),
            }
    except Exception as e:
        return False, None, {"error": str(e)[:160]}


@router.post("/server/diagnose", response_model=ServerConnection)
async def diagnose(req: ServerProbeRequest):
    host = (req.host or "").strip()
    if not host:
        raise HTTPException(status_code=400, detail="empty_host")
    protocol = (req.protocol or "https").lower().strip()
    port = req.port or DEFAULT_PORTS.get(protocol, 443)

    # DNS resolve
    dns_ip = None
    try:
        loop = asyncio.get_event_loop()
        infos = await loop.run_in_executor(
            None, lambda: socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        )
        if infos:
            dns_ip = infos[0][4][0]
    except Exception:
        dns_ip = None

    # TCP probe (always)
    tcp_ok, tcp_lat, tcp_err = await asyncio.get_event_loop().run_in_executor(
        None, _tcp_probe, host, port
    )

    details = {
        "dns_ip": dns_ip,
        "tcp_ok": tcp_ok,
        "tcp_latency_ms": round(tcp_lat, 2) if tcp_lat else None,
        "tcp_error": tcp_err,
        "default_port": DEFAULT_PORTS.get(protocol),
    }

    if protocol in ("http", "https"):
        http_ok, http_lat, http_meta = await _http_probe(protocol, host, port)
        details["http_ok"] = http_ok
        details["http_latency_ms"] = round(http_lat, 2) if http_lat else None
        details["http_info"] = http_meta
        latency = http_lat if http_lat else tcp_lat
        status = "REACHABLE" if (http_ok or tcp_ok) else "UNREACHABLE"
    else:
        details["note"] = (
            f"{protocol.upper()} probe is TCP-only — Althea will not attempt "
            "credentialed connections without operator cryptographic approval."
        )
        latency = tcp_lat
        status = "REACHABLE" if tcp_ok else "UNREACHABLE"
        if protocol not in ("http", "https"):
            status = "GATED" if tcp_ok else "UNREACHABLE"

    conn = ServerConnection(
        host=host,
        port=port,
        protocol=protocol,
        status=status,
        latency_ms=round(latency, 2) if latency else None,
        details=details,
    )
    doc = conn.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_servers.insert_one(doc)

    # Memory + notification
    mem = Memory(
        content=(
            f"[SERVER-PROBE {protocol.upper()}://{host}:{port}] {status} "
            f"dns:{dns_ip or '-'} tcp:{tcp_ok} lat:{round(latency, 2) if latency else '-'}ms"
        ),
        source="server",
        tags=["server", "probe", protocol],
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)

    await emit_notification(
        title=f"server · {host}:{port} · {status}",
        body=(
            f"{protocol.upper()} probe complete. "
            + (f"latency {round(latency, 2)}ms · " if latency else "")
            + (f"dns {dns_ip}" if dns_ip else "no DNS")
        ),
        category="server",
        priority="warn" if status == "UNREACHABLE" else "info",
        payload={"host": host, "port": port, "status": status},
    )

    return conn


@router.get("/server/connections", response_model=List[ServerConnection])
async def list_servers(limit: int = 100):
    docs = await db.althea_servers.find({}, {"_id": 0}).sort(
        "timestamp", -1
    ).to_list(limit)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.delete("/server/connections/{conn_id}")
async def remove_server(conn_id: str):
    res = await db.althea_servers.delete_one({"id": conn_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"deleted": conn_id}


@router.delete("/server/connections")
async def clear_servers():
    res = await db.althea_servers.delete_many({})
    return {"deleted": res.deleted_count}
