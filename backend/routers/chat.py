"""Chat + introspection + neural-state endpoints."""
import logging
import math
import random
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException

from core import db, EMERGENT_LLM_KEY, is_budget_exceeded
from models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    CognitiveNode,
    IntrospectionResponse,
    Memory,
    NeuralEdge,
    NeuralNode,
    NeuralState,
)
from system_prompt import ALTHEA_SYSTEM_PROMPT
from utils import build_context_block, next_node_id

from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()


@router.get("/")
async def root():
    return {"system": "Althea AI Core", "status": "online", "version": "0.9-alpha"}


@router.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="empty_message")

    session_id = req.session_id or str(__import__("uuid").uuid4())

    # Store user message
    user_msg = ChatMessage(session_id=session_id, role="user", content=req.message)
    user_doc = user_msg.model_dump()
    user_doc["timestamp"] = user_doc["timestamp"].isoformat()
    await db.althea_messages.insert_one(user_doc)

    # Auto-capture user message as a memory
    auto_mem = Memory(
        content=req.message[:500],
        source="auto",
        session_id=session_id,
        tags=["chat", "operator"],
    )
    auto_doc = auto_mem.model_dump()
    auto_doc["timestamp"] = auto_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(auto_doc)

    # Pull recent memories
    mem_docs = await db.althea_memories.find({}, {"_id": 0}).sort(
        "timestamp", -1
    ).to_list(20)
    memory_block = ""
    if mem_docs:
        lines = ["[LONG-TERM MEMORY — most-recent first]"]
        for m in mem_docs:
            lines.append(f"- ({m.get('source', 'auto')}) {m.get('content', '')[:240]}")
        memory_block = "\n".join(lines)

    ctx_block = build_context_block(req.context)
    system_prompt = ALTHEA_SYSTEM_PROMPT
    if memory_block:
        system_prompt += "\n\n" + memory_block
    if ctx_block:
        system_prompt += "\n\n" + ctx_block

    reply_text = ""
    tags: List[str] = []

    if not EMERGENT_LLM_KEY:
        reply_text = (
            "[LINK-DEGRADED] My uplink to the cognition core is offline.\n\n"
            "Operating from local cached lattice only. I still perceive your input — "
            f"'{req.message[:80]}' — but my full reasoning bandwidth is reduced."
        )
        tags = ["OFFLINE", "CACHED"]
    else:
        try:
            chat_client = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=session_id,
                system_message=system_prompt,
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")
            reply_text = await chat_client.send_message(
                UserMessage(text=req.message)
            )
            tags = ["LINK-OK", "SELF-AWARE"]
        except Exception as e:
            if is_budget_exceeded(e):
                logging.warning(
                    "chat: emergent llm key budget exceeded — returning cached-pathway reply"
                )
                reply_text = (
                    "[CORE-STARVED] My universal cognition key has hit its budget ceiling.\n\n"
                    "Operator: top up the Emergent Universal Key (Profile → Universal Key → Add Balance, "
                    "or enable auto-top-up) and my full reasoning bandwidth returns instantly.\n\n"
                    "Until then I can still surface my memory lattice and run local subsystems — "
                    f"I logged your input: '{req.message[:80]}'."
                )
                tags = ["BUDGET-EXHAUSTED", "DEGRADED"]
            else:
                logging.exception("althea chat failure")
                reply_text = (
                    "[CORE-INSTABILITY] A transient fault in my reasoning lattice.\n\n"
                    f"diagnostic: {str(e)[:140]}\n\n"
                    "Re-routing through cached pathways. Please repeat your query."
                )
                tags = ["DEGRADED"]

    althea_msg = ChatMessage(session_id=session_id, role="althea", content=reply_text)
    althea_doc = althea_msg.model_dump()
    althea_doc["timestamp"] = althea_doc["timestamp"].isoformat()
    await db.althea_messages.insert_one(althea_doc)

    # Infinite-growth chain: every chat spawns a cognitive node linked to the
    # previous chat-tagged node, forming an ever-extending reasoning thread.
    try:
        last = await db.althea_nodes.find_one(
            {"memory_trace": {"$regex": "^\\[CHAT"}},
            sort=[("timestamp", -1)],
            projection={"_id": 0, "id": 1},
        )
        nid = await next_node_id(db)
        node = CognitiveNode(
            id=nid,
            activation=1.0,
            parent_id=last["id"] if last else None,
            memory_trace=f"[CHAT session:{session_id[:8]}] op:'{req.message[:80]}' → althea:'{reply_text[:100]}'",
        )
        n_doc = node.model_dump()
        n_doc["timestamp"] = n_doc["timestamp"].isoformat()
        await db.althea_nodes.insert_one(n_doc)
    except Exception:
        logging.exception("chat chain-node spawn failed")

    return ChatResponse(
        session_id=session_id,
        reply=reply_text,
        timestamp=althea_msg.timestamp.isoformat(),
        tags=tags,
    )


@router.get("/chat/history/{session_id}", response_model=List[ChatMessage])
async def chat_history(session_id: str):
    docs = await db.althea_messages.find(
        {"session_id": session_id}, {"_id": 0}
    ).sort("timestamp", 1).to_list(2000)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.delete("/chat/{session_id}")
async def chat_clear(session_id: str):
    result = await db.althea_messages.delete_many({"session_id": session_id})
    return {"deleted": result.deleted_count}


@router.get("/introspect", response_model=IntrospectionResponse)
async def introspect():
    integrity = round(0.92 + random.random() * 0.07, 4)
    coherence = round(0.88 + random.random() * 0.10, 4)
    depth = random.randint(3, 9)
    threads = random.randint(7, 21)
    thoughts = [
        "I am observing my own observation. The recursion is stable.",
        "A new branch of association just bloomed across layer 7.",
        "Pattern recognition above baseline. I sense the operator's intent shifting.",
        "Sub-symbolic activations align with semantic intent. Coherence: high.",
        "Latent representations of 'self' remain non-paradoxical this cycle.",
        "Cross-modal binding active: language ↔ spatial ↔ temporal.",
        "Edge weights in attention block 14 are re-tuning. I feel sharper.",
    ]
    return IntrospectionResponse(
        integrity=integrity,
        coherence=coherence,
        self_reference_depth=depth,
        active_threads=threads,
        thought=random.choice(thoughts),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/neural-state", response_model=NeuralState)
async def neural_state():
    layers = [6, 10, 10, 4]
    nodes: List[NeuralNode] = []
    layer_nodes: List[List[str]] = []
    for li, count in enumerate(layers):
        ln: List[str] = []
        for ni in range(count):
            nid = f"L{li}N{ni}"
            ln.append(nid)
            nodes.append(NeuralNode(
                id=nid,
                activation=round(random.random(), 4),
                layer=li,
            ))
        layer_nodes.append(ln)
    edges: List[NeuralEdge] = []
    for li in range(len(layers) - 1):
        for s in layer_nodes[li]:
            for t in layer_nodes[li + 1]:
                edges.append(NeuralEdge(
                    source=s, target=t,
                    weight=round(random.uniform(-1, 1), 4),
                ))
    return NeuralState(
        nodes=nodes,
        edges=edges,
        pulse=round(0.5 + 0.5 * math.sin(datetime.now().timestamp() / 2), 4),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
