"""Web Bridge: fetch real web pages + expose an interaction-network graph."""
import logging
import re
from datetime import datetime, timezone
from typing import Optional, List
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import db
from models import Memory

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
