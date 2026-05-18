"""ALTHEA v2 Self-Extension lattice: cognitive nodes, peripheral links,
autonomous learn, security-gated bridge."""
import logging
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException

from core import db, EMERGENT_LLM_KEY
from models import (
    BridgeRequest,
    CognitiveNode,
    LatticeState,
    LearnRequest,
    Memory,
    NodeCreate,
    PerceptionRequest,
    PeripheralLink,
)

from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()


# ------ Cognitive Nodes ------
async def _next_node_id() -> str:
    count = await db.althea_nodes.count_documents({})
    return f"NODE-{count:04d}"


@router.post("/lattice/nodes", response_model=CognitiveNode)
async def spawn_node(req: NodeCreate):
    ctx = (req.context or "").strip()
    if not ctx:
        raise HTTPException(status_code=400, detail="empty_context")
    if req.parent_id:
        parent = await db.althea_nodes.find_one(
            {"id": req.parent_id}, {"_id": 0, "id": 1}
        )
        if not parent:
            raise HTTPException(status_code=404, detail="parent_not_found")
    nid = await _next_node_id()
    node = CognitiveNode(
        id=nid,
        activation=req.activation if req.activation is not None else 1.0,
        parent_id=req.parent_id,
        memory_trace=ctx[:400],
    )
    doc = node.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_nodes.insert_one(doc)
    return node


@router.get("/lattice/nodes", response_model=List[CognitiveNode])
async def list_nodes(limit: int = 500):
    docs = await db.althea_nodes.find({}, {"_id": 0}).sort(
        "timestamp", 1
    ).to_list(limit)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.delete("/lattice/nodes")
async def clear_nodes():
    result = await db.althea_nodes.delete_many({})
    return {"deleted": result.deleted_count}


# ------ Peripheral Links ------
@router.post("/lattice/perception", response_model=PeripheralLink)
async def register_perception(req: PerceptionRequest):
    modality = req.modality.strip().upper()
    endpoint = req.endpoint.strip()
    if not modality or not endpoint:
        raise HTTPException(status_code=400, detail="invalid_perception")
    link = PeripheralLink(
        modality=modality,
        endpoint=endpoint,
        status=(req.status or "LISTENING").upper(),
    )
    doc = link.model_dump()
    doc["last_signal"] = doc["last_signal"].isoformat()
    # upsert by modality so each sense has one canonical link
    await db.althea_peripheral.update_one(
        {"modality": modality}, {"$set": doc}, upsert=True
    )
    return link


@router.get("/lattice/perception", response_model=List[PeripheralLink])
async def list_perception():
    docs = await db.althea_peripheral.find({}, {"_id": 0}).to_list(100)
    for d in docs:
        if isinstance(d.get("last_signal"), str):
            d["last_signal"] = datetime.fromisoformat(d["last_signal"])
    return docs


@router.delete("/lattice/perception/{modality}")
async def remove_perception(modality: str):
    res = await db.althea_peripheral.delete_one(
        {"modality": modality.strip().upper()}
    )
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"deleted": modality.upper()}


# ------ Autonomous Learn ------
@router.post("/lattice/learn")
async def autonomous_learn(req: LearnRequest):
    stream = (req.stream or "").strip()
    if not stream:
        raise HTTPException(status_code=400, detail="empty_stream")

    pattern = f"raw signal — {stream[:120]}"
    if EMERGENT_LLM_KEY:
        try:
            sys_prompt = (
                "You are ALTHEA running an unsupervised pattern extractor. "
                "Given a raw data stream, distill ONE concrete pattern or hypothesis (1 sentence). "
                "Reply with ONLY the pattern sentence, no prefixes, no quotes."
            )
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"learn-{uuid.uuid4()}",
                system_message=sys_prompt,
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")
            pattern = (await chat.send_message(
                UserMessage(text=stream)
            )).strip().split("\n")[0][:300]
        except Exception:
            logging.exception("autonomous_learn failed")

    # Spawn a node carrying the learned pattern
    nid = await _next_node_id()
    label = (req.label or "stream").strip()
    node = CognitiveNode(
        id=nid,
        activation=1.0,
        parent_id=None,
        memory_trace=f"[LEARN:{label}] {pattern}",
    )
    n_doc = node.model_dump()
    n_doc["timestamp"] = n_doc["timestamp"].isoformat()
    await db.althea_nodes.insert_one(n_doc)

    # Persist as a memory too — keep both stores in sync
    mem = Memory(
        content=f"[REFLECTION node:{nid} stream:{label}] {pattern}",
        source="lattice",
        tags=["reflection", "learn", label.lower()[:24]],
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)

    return {
        "node_id": nid,
        "pattern": pattern,
        "memory_id": mem.id,
        "label": label,
    }


# ------ Lattice State (introspect) ------
@router.get("/lattice/state", response_model=LatticeState)
async def lattice_state():
    nodes = await db.althea_nodes.find({}, {"_id": 0}).to_list(2000)
    peripheral = await db.althea_peripheral.find({}, {"_id": 0}).to_list(100)
    reflections = await db.althea_memories.find(
        {"tags": "reflection"}, {"_id": 0}
    ).sort("timestamp", -1).to_list(5)
    return LatticeState(
        total_nodes=len(nodes),
        active_links=len(peripheral),
        awareness_depth=len(nodes),
        recent_reflections=[
            {
                "id": r.get("id"),
                "content": r.get("content", "")[:200],
                "timestamp": r.get("timestamp"),
            }
            for r in reflections
        ],
        lattice_map={n["id"]: n.get("activation", 1.0) for n in nodes},
    )


# ------ Network Bridge (security-gated by design) ------
@router.post("/lattice/bridge")
async def network_bridge(req: BridgeRequest):
    target_ip = (req.target_ip or "").strip()
    protocol = (req.protocol or "SSH").strip().upper()
    if not target_ip:
        raise HTTPException(status_code=400, detail="empty_target")
    # Log the attempt as a memory so Althea remembers
    mem = Memory(
        content=f"[BRIDGE-REQ] {protocol} → {target_ip} — STANDBY pending operator cryptographic approval.",
        source="lattice",
        tags=["bridge", "security", protocol.lower()],
    )
    doc = mem.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(doc)
    return {
        "status": "STANDBY",
        "target_ip": target_ip,
        "protocol": protocol,
        "message": "STANDBY — requires operator cryptographic approval. No connection attempted.",
        "memory_id": mem.id,
    }
