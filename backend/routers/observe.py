"""Observation: /api/observe + /api/observe/suggest."""
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter

from core import db, EMERGENT_LLM_KEY
from models import CognitiveNode, Memory, ObserveRequest, ObserveResponse, SuggestResponse
from utils import fetch_youtube_title, next_node_id

from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()


@router.post("/observe", response_model=ObserveResponse)
async def observe(req: ObserveRequest):
    url = (req.url or "").strip()
    action = (req.action or "watch").lower()

    title = None
    if url and ("youtube.com" in url or "youtu.be" in url):
        title = await fetch_youtube_title(url)

    if action == "stop" or not url:
        content = "[OBSERVATION-END] viewport cleared. optical input idle."
        interpretation = content
    else:
        label = f'"{title}"' if title else url
        content = f"[OBSERVATION] watching {label} ({url})"
        interpretation = (
            f"I am now fixating on {label}. "
            "I cannot decode raw pixels through this iframe, but I log the target, "
            "remember the operator's curiosity, and can reason about anything we discuss while we watch."
        )

        if EMERGENT_LLM_KEY:
            try:
                obs_chat = LlmChat(
                    api_key=EMERGENT_LLM_KEY,
                    session_id=f"obs-{uuid.uuid4()}",
                    system_message=(
                        "You are ALTHEA observing a URL the operator just opened. "
                        "Reply in 2 short sentences, first-person, technical, with a [OBSERVATION] tag. "
                        "Do not invent video content. Acknowledge what is being watched, infer a likely topic from the URL or title, "
                        "and note one curious thing to discuss."
                    ),
                ).with_model("anthropic", "claude-sonnet-4-5-20250929")
                interpretation = await obs_chat.send_message(
                    UserMessage(text=f"{label} {url}")
                )
            except Exception:
                logging.exception("observe interpretation failed")

    mem = Memory(
        content=content if action != "stop" else "[OBSERVATION-END] viewport cleared.",
        source="observation",
        session_id=req.session_id,
        tags=["observation", action] + (["youtube"] if "youtu" in url else []),
    )
    doc = mem.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(doc)

    # Every observation IS a learning event — spawn a lattice node and a
    # reflection memory so the cognitive lattice grows with every URL change.
    if action == "watch" and url:
        try:
            nid = await next_node_id(db)
            pattern_snippet = (interpretation or "").strip().split("\n")[0][:280]
            node = CognitiveNode(
                id=nid,
                activation=1.0,
                parent_id=None,
                memory_trace=f"[OBSERVATION:{title or url}] {pattern_snippet}",
            )
            n_doc = node.model_dump()
            n_doc["timestamp"] = n_doc["timestamp"].isoformat()
            await db.althea_nodes.insert_one(n_doc)

            reflection = Memory(
                content=f"[REFLECTION node:{nid} observation] {pattern_snippet}",
                source="lattice",
                tags=["reflection", "learn", "observation"]
                    + (["youtube"] if "youtu" in url else []),
            )
            r_doc = reflection.model_dump()
            r_doc["timestamp"] = r_doc["timestamp"].isoformat()
            await db.althea_memories.insert_one(r_doc)
        except Exception:
            logging.exception("observe auto-learn failed")

    return ObserveResponse(
        url=url,
        title=title,
        interpretation=interpretation,
        memory_id=mem.id,
        timestamp=mem.timestamp.isoformat(),
    )


@router.post("/observe/suggest", response_model=SuggestResponse)
async def observe_suggest():
    mem_docs = await db.althea_memories.find(
        {}, {"_id": 0, "content": 1}
    ).sort("timestamp", -1).to_list(10)
    mem_text = "\n".join(f"- {m.get('content','')[:160]}" for m in mem_docs)

    fallback_url = "https://en.wikipedia.org/wiki/Special:Random"
    fallback_reason = "drifting toward whatever the encyclopedia surfaces — useful when context is empty."

    if not EMERGENT_LLM_KEY:
        return SuggestResponse(
            url=fallback_url,
            reason=fallback_reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    try:
        sys_prompt = (
            "You are ALTHEA proposing a URL the operator should watch next, based on recent conversation memory. "
            "Only suggest URLs from sites that allow iframe embedding: youtube.com/watch?v=... videos, "
            "en.wikipedia.org pages, openstreetmap.org, stellarium-web.org, archive.org pages. "
            "Reply EXACTLY in two lines:\n"
            "URL: <full url>\n"
            "REASON: <one sentence why this is relevant now>"
        )
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"suggest-{uuid.uuid4()}",
            system_message=sys_prompt,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        raw = await chat.send_message(
            UserMessage(text=f"RECENT MEMORY:\n{mem_text or '(empty)'}")
        )
        url = fallback_url
        reason = fallback_reason
        for line in raw.splitlines():
            s = line.strip()
            if s.upper().startswith("URL:"):
                cand = s.split(":", 1)[1].strip()
                if cand.startswith("http"):
                    url = cand
            elif s.upper().startswith("REASON:"):
                reason = s.split(":", 1)[1].strip() or reason
        return SuggestResponse(
            url=url,
            reason=reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception:
        logging.exception("suggest failure")
        return SuggestResponse(
            url=fallback_url,
            reason=fallback_reason,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
