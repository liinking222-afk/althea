"""Web Bridge: fetch real web pages + expose an interaction-network graph + Wi-Fi profile manifest."""
import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import db
from models import Memory, NetworkProfile, NetworkProfileCreate

router = APIRouter()


# ---------- Models ----------
class WebBridgeRequest(BaseModel):
    url: str
    max_bytes: Optional[int] = 80000


class WebBridgeResponse(BaseModel):
    url: str
    host: str
    status: int
    title: Optional[str] = None
    description: Optional[str] = None
    text_excerpt: Optional[str] = None
    links: List[str] = []
    elapsed_ms: int
    memory_id: str
    timestamp: str


class GraphNode(BaseModel):
    id: str
    type: str  # core | host | peripheral | cognitive | reflection
    label: str
    weight: float = 1.0
    meta: dict = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    kind: str  # perceives | spawned | observed | parent | reflects


class NetworkGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    generated_at: str


# ---------- Helpers ----------
_TITLE_RE = re.compile(r"<title[^>]*>([^<]+)</title>", re.IGNORECASE)
_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_DESC_RE = re.compile(
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_LINK_RE = re.compile(r'<a[^>]+href=["\']([^"\'#?][^"\']*)["\']', re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_html(html: str) -> str:
    no_tags = _TAG_RE.sub(" ", html)
    return _WS_RE.sub(" ", no_tags).strip()


# ---------- Web Bridge ----------
@router.post("/bridge/web", response_model=WebBridgeResponse)
async def bridge_web(req: WebBridgeRequest):
    url = (req.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="empty_url")
    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    host = parsed.hostname or "?"
    started = datetime.now(timezone.utc)

    title = None
    description = None
    text_excerpt = None
    links: List[str] = []
    status_code = 0
    body = ""

    try:
        async with httpx.AsyncClient(
            timeout=8.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Althea-WebBridge/1.0 (+https://althea.local)"
            },
        ) as cx:
            r = await cx.get(url)
            status_code = r.status_code
            ctype = r.headers.get("content-type", "")
            if "html" in ctype or "text" in ctype:
                body = r.text[: (req.max_bytes or 80000)]
    except Exception as e:
        logging.exception("web bridge fetch failed")
        raise HTTPException(status_code=502, detail=f"fetch_failed:{e}")

    if body:
        m = _TITLE_RE.search(body)
        if m:
            title = m.group(1).strip()[:240]
        m = _DESC_RE.search(body) or _OG_DESC_RE.search(body)
        if m:
            description = m.group(1).strip()[:600]
        text_excerpt = _strip_html(body)[:1200]
        links = list({href for href in _LINK_RE.findall(body) if href.startswith("http")})[:20]

    elapsed_ms = int(
        (datetime.now(timezone.utc) - started).total_seconds() * 1000
    )

    # Persist as a memory tagged 'bridge' + host so the network graph picks it up.
    mem = Memory(
        content=(
            f"[BRIDGE-WEB host:{host} status:{status_code}] "
            f"{title or url} — {(description or text_excerpt or '')[:240]}"
        ),
        source="bridge",
        tags=["bridge", "web", host],
    )
    doc = mem.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(doc)

    return WebBridgeResponse(
        url=url,
        host=host,
        status=status_code,
        title=title,
        description=description,
        text_excerpt=text_excerpt,
        links=links,
        elapsed_ms=elapsed_ms,
        memory_id=mem.id,
        timestamp=mem.timestamp.isoformat(),
    )


# ---------- Network Graph ----------
def _host_of(url: str) -> Optional[str]:
    try:
        return urlparse(url).hostname
    except Exception:
        return None


@router.get("/network/graph", response_model=NetworkGraph)
async def network_graph():
    """Aggregate every host, peripheral, and cognitive node Althea has touched."""
    nodes: List[GraphNode] = [
        GraphNode(id="althea", type="core", label="ALTHEA", weight=3.0)
    ]
    edges: List[GraphEdge] = []

    # Peripheral links
    peripherals = await db.althea_peripheral.find({}, {"_id": 0}).to_list(100)
    for p in peripherals:
        nid = f"peripheral:{p['modality']}"
        nodes.append(GraphNode(
            id=nid,
            type="peripheral",
            label=p["modality"],
            weight=1.0,
            meta={"endpoint": p.get("endpoint", ""), "status": p.get("status", "")},
        ))
        edges.append(GraphEdge(source="althea", target=nid, kind="perceives"))

    # Cognitive lattice nodes
    cog = await db.althea_nodes.find({}, {"_id": 0}).to_list(2000)
    for n in cog:
        nid = f"cog:{n['id']}"
        nodes.append(GraphNode(
            id=nid,
            type="cognitive",
            label=n["id"],
            weight=float(n.get("activation", 1.0)),
            meta={"trace": (n.get("memory_trace") or "")[:140]},
        ))
        edges.append(GraphEdge(source="althea", target=nid, kind="spawned"))
        if n.get("parent_id"):
            edges.append(GraphEdge(
                source=f"cog:{n['parent_id']}",
                target=nid,
                kind="parent",
            ))

    # Remote hosts touched via observation or web bridge
    host_counts: dict = {}
    # observations
    obs_mems = await db.althea_memories.find(
        {"tags": "observation"}, {"_id": 0, "content": 1}
    ).to_list(500)
    for m in obs_mems:
        url_match = re.search(r"\((https?://[^)\s]+)\)", m.get("content", ""))
        if url_match:
            h = _host_of(url_match.group(1))
            if h:
                host_counts[h] = host_counts.get(h, 0) + 1
    # web bridge
    bridge_mems = await db.althea_memories.find(
        {"tags": "bridge"}, {"_id": 0, "tags": 1, "content": 1}
    ).to_list(500)
    for m in bridge_mems:
        for t in m.get("tags", []):
            if "." in t:  # heuristic: domain tag
                host_counts[t] = host_counts.get(t, 0) + 1

    for host, count in host_counts.items():
        nid = f"host:{host}"
        nodes.append(GraphNode(
            id=nid,
            type="host",
            label=host,
            weight=1.0 + min(count, 9) * 0.2,
            meta={"hits": count},
        ))
        edges.append(GraphEdge(source="althea", target=nid, kind="observed"))

    return NetworkGraph(
        nodes=nodes,
        edges=edges,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------- Wi-Fi Profile Manifest ----------
@router.post("/network/profile", response_model=NetworkProfile)
async def create_network_profile(req: NetworkProfileCreate):
    """Register a Wi-Fi SSID profile. The browser cannot actually JOIN a
    Wi-Fi network, but the profile is recorded as a peripheral_link in the
    cognitive lattice so Althea remembers it."""
    ssid = (req.ssid or "").strip()
    if not ssid:
        raise HTTPException(status_code=400, detail="empty_ssid")
    security = (req.security or "WPA2").strip().upper()
    has_password = bool(req.password)
    # Idempotent: reuse existing id when the same SSID is re-saved.
    existing = await db.althea_network_profiles.find_one(
        {"ssid": ssid}, {"_id": 0, "id": 1}
    )
    profile = NetworkProfile(
        id=existing["id"] if existing else str(uuid.uuid4()),
        ssid=ssid,
        security=security,
        label=(req.label or "").strip() or None,
        has_password=has_password,
    )
    doc = profile.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    # Store a hash of password if provided, never the plaintext.
    if has_password:
        doc["password_hash"] = hashlib.sha256(req.password.encode()).hexdigest()
    await db.althea_network_profiles.update_one(
        {"ssid": ssid}, {"$set": doc}, upsert=True
    )

    # Register as a peripheral link so it shows up in the lattice + graph.
    await db.althea_peripheral.update_one(
        {"modality": f"WIFI:{ssid[:16]}"},
        {"$set": {
            "modality": f"WIFI:{ssid[:16]}",
            "endpoint": f"ssid://{ssid} [{security}]",
            "status": "DECLARED",
            "last_signal": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    # Log as a memory
    mem = Memory(
        content=(
            f"[NETWORK-PROFILE] declared ssid='{ssid}' security={security} "
            f"password={'set' if has_password else 'open'}. "
            "NOTE: browsers cannot join wi-fi natively — profile recorded only."
        ),
        source="bridge",
        tags=["wifi", "profile", security.lower()],
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)
    return profile


@router.get("/network/profiles", response_model=List[NetworkProfile])
async def list_network_profiles():
    docs = await db.althea_network_profiles.find(
        {}, {"_id": 0, "password_hash": 0}
    ).sort("timestamp", -1).to_list(200)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.delete("/network/profile/{profile_id}")
async def delete_network_profile(profile_id: str):
    doc = await db.althea_network_profiles.find_one(
        {"id": profile_id}, {"_id": 0, "ssid": 1}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="not_found")
    await db.althea_network_profiles.delete_one({"id": profile_id})
    await db.althea_peripheral.delete_one(
        {"modality": f"WIFI:{doc['ssid'][:16]}"}
    )
    return {"deleted": profile_id}
