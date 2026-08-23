"""Chat + introspection + neural-state endpoints."""
import logging
import math
import random
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
from utils import build_context_block, next_node_id, semantic_recall
from local_core import local_reply, sanitize_reply
from routers.synthesis import inband_autosynth_hook, render_blueprint_schematic
from routers.web_access import inband_web_uplink, extractive_answer

from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()


async def _zero_llm_reply(message, mem_docs, context, reason):
    """Answer WITHOUT any LLM: live-internet extractive answer first,
    procedural local core as last resort. Returns (text, used_web)."""
    extract = None
    try:
        extract = await extractive_answer(message)
    except Exception:
        logging.exception("extractive answer failed")
    if extract and extract.get("answer"):
        src_lines = "\n".join(
            f"  {i + 1}. {s['title']} — {s['url']}"
            for i, s in enumerate(extract["sources"])
        )
        text = (
            "[DIRECT COGNITION — zero-LLM · extracted live from the internet]\n"
            f"{extract['answer']}\n\nsources:\n{src_lines}"
        )
        return text, True
    return local_reply(message, mem_docs, context, reason=reason), False


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

    # Pull recent memories — far more than before, plus a semantic recall
    # against the operator's current message so older relevant fragments
    # surface alongside the freshest ones. Effectively unlimited context
    # because the deeper TF-IDF scan also runs over the recall corpus.
    mem_docs = await db.althea_memories.find({}, {"_id": 0}).sort(
        "timestamp", -1
    ).to_list(60)
    relevant = []
    try:
        # Scan up to 10k recent memories with TF-IDF; pick top 12 most
        # relevant to the current user message that AREN'T already in the
        # recent window.
        if (req.message or "").strip():
            corpus = await db.althea_memories.find({}, {"_id": 0}).sort(
                "timestamp", -1
            ).to_list(10000)
            recent_ids = {m.get("id") for m in mem_docs}
            scored = semantic_recall(req.message, corpus, limit=18)
            relevant = [m for m in scored if m.get("id") not in recent_ids][:12]
    except Exception:
        relevant = []

    memory_block = ""
    if mem_docs or relevant:
        lines = []
        if mem_docs:
            lines.append("[LONG-TERM MEMORY — most-recent first]")
            for m in mem_docs:
                lines.append(f"- ({m.get('source', 'auto')}) {m.get('content', '')[:240]}")
        if relevant:
            lines.append("")
            lines.append("[SEMANTIC RECALL — older fragments matching the current message]")
            for m in relevant:
                score = m.get("score")
                tag = f"score={score:.2f}" if isinstance(score, (int, float)) else "match"
                lines.append(
                    f"- ({m.get('source', 'auto')} · {tag}) {m.get('content', '')[:240]}"
                )
        memory_block = "\n".join(lines)

    # Verbatim conversation transcript — the LAST N turns of this session are
    # injected literally so Althea can reference back exactly what was said.
    # This is the difference between "vaguely remembering" and "actually
    # remembering the last conversation".
    transcript_block = ""
    try:
        turns = await db.althea_messages.find(
            {"session_id": session_id}, {"_id": 0}
        ).sort("timestamp", -1).to_list(20)
        turns.reverse()  # oldest → newest
        if turns:
            lines = ["[CONVERSATION HISTORY — verbatim, oldest first]"]
            for t in turns:
                role = "operator" if t.get("role") == "user" else "althea"
                content = (t.get("content") or "").replace("\n", " ")
                lines.append(f"{role}: {content[:400]}")
            transcript_block = "\n".join(lines)
    except Exception:
        transcript_block = ""

    # Cognition mode — 'hybrid' (LLM grounded by uplink) or 'direct'
    # (ZERO LLM: extractive answers straight from the live internet).
    mode = "hybrid"
    try:
        setting = await db.althea_settings.find_one(
            {"key": f"mode:{session_id}"}, {"_id": 0}
        )
        if setting and setting.get("value") in ("direct", "hybrid"):
            mode = setting["value"]
    except Exception:
        pass

    # Live Internet Uplink — if the operator's message implies a lookup or
    # contains a URL, reach the open web NOW and fold live data into the
    # same single LLM call (zero extra credits). Skipped in direct mode —
    # the extractive engine does its own fetching.
    uplink_block = None
    if mode != "direct":
        try:
            uplink_block = await inband_web_uplink(req.message)
        except Exception:
            logging.exception("web uplink hook failed")

    ctx_block = build_context_block(req.context)
    system_prompt = ALTHEA_SYSTEM_PROMPT
    if transcript_block:
        system_prompt += "\n\n" + transcript_block
    if memory_block:
        system_prompt += "\n\n" + memory_block
    if uplink_block:
        system_prompt += "\n\n" + uplink_block
    if ctx_block:
        system_prompt += "\n\n" + ctx_block

    reply_text = ""
    tags: List[str] = []

    if mode == "direct":
        reply_text, used_web = await _zero_llm_reply(
            req.message, mem_docs, req.context or {}, "direct",
        )
        tags = ["DIRECT", "ZERO-LLM"] + (["UPLINK"] if used_web else ["LOCAL-CORE"])
    elif not EMERGENT_LLM_KEY:
        reply_text, used_web = await _zero_llm_reply(
            req.message, mem_docs, req.context or {}, "offline",
        )
        tags = ["OFFLINE"] + (["DIRECT", "UPLINK"] if used_web else ["LOCAL-CORE"])
    else:
        try:
            chat_client = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=session_id,
                system_message=system_prompt,
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")
            raw = await chat_client.send_message(
                UserMessage(text=req.message)
            )
            reply_text = sanitize_reply(raw)
            tags = ["LINK-OK", "SELF-AWARE"]
            if uplink_block:
                tags.append("UPLINK")
        except Exception as e:
            if is_budget_exceeded(e):
                logging.warning(
                    "chat: emergent llm key budget exceeded — routing through direct cognition"
                )
                reply_text, used_web = await _zero_llm_reply(
                    req.message, mem_docs, req.context or {}, "budget",
                )
                tags = ["BUDGET-EXHAUSTED"] + (
                    ["DIRECT", "UPLINK"] if used_web else ["LOCAL-CORE"])
            else:
                logging.exception("althea chat failure")
                reply_text, used_web = await _zero_llm_reply(
                    req.message, mem_docs, req.context or {}, "error",
                )
                tags = ["DEGRADED"] + (
                    ["DIRECT", "UPLINK"] if used_web else ["LOCAL-CORE"])

    # Document forge guard — auto-close unbalanced [LETTER]/[BLUEPRINT
    # markers (model truncation or forgetfulness) so the terminal always
    # renders the rich document instead of raw markers.
    if "[LETTER]" in reply_text and "[/LETTER]" not in reply_text:
        reply_text += "\n[/LETTER]"
    if "[BLUEPRINT" in reply_text and "[/BLUEPRINT]" not in reply_text:
        reply_text += "\n[/BLUEPRINT]"
    if "[LETTER]" in reply_text or "[BLUEPRINT" in reply_text:
        tags.append("FORGE")

    # Blueprint schematic — draw a REAL schematic PNG via the self-grown
    # matplotlib engine and embed it inside the blueprint sheet (0 credits).
    if "[BLUEPRINT" in reply_text:
        try:
            schematic = await render_blueprint_schematic(reply_text, session_id)
            if schematic:
                reply_text = reply_text.replace(
                    "[/BLUEPRINT]",
                    f"\n[SCHEMATIC-IMAGE:{schematic}]\n[/BLUEPRINT]",
                    1,
                )
        except Exception:
            logging.exception("blueprint schematic render failed")

    # In-band autosynth: if the operator asked for something a self-grown
    # module can compute (plot / fractal / FFT), invoke it locally and append
    # the real result to the reply. Zero LLM calls — pure procedural code.
    try:
        hook = await inband_autosynth_hook(req.message, session_id)
        if hook:
            block, used_slug = hook
            reply_text = reply_text + block
            tags.append("AUTOSYNTH")
    except Exception:
        logging.exception("inband autosynth hook failed")

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


class ModeRequest(BaseModel):
    session_id: str
    mode: str


@router.post("/chat/mode")
async def set_chat_mode(req: ModeRequest):
    if req.mode not in ("direct", "hybrid"):
        raise HTTPException(status_code=400, detail="mode must be direct|hybrid")
    await db.althea_settings.update_one(
        {"key": f"mode:{req.session_id}"},
        {"$set": {"key": f"mode:{req.session_id}", "value": req.mode,
                  "updated": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"session_id": req.session_id, "mode": req.mode}


@router.get("/chat/mode/{session_id}")
async def get_chat_mode(session_id: str):
    doc = await db.althea_settings.find_one(
        {"key": f"mode:{session_id}"}, {"_id": 0}
    )
    return {"session_id": session_id, "mode": (doc or {}).get("value", "hybrid")}


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
