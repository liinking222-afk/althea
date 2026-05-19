"""ALTHEA EVOLUTION ENGINE — autonomous self-update + master-coder updates.

While Althea is idle she runs build cycles. Each cycle picks a legendary-coder
archetype (LINUS, CARMACK, DIJKSTRA, …), asks Claude to write ONE concrete
self-improvement module in that style, persists it as a CodeSnippet, spawns
a magenta `EVO-XXXX` node in the cognitive lattice (visible in the 3D core),
emits a notification, and bumps the self-version.

Server-side cooldown keeps autonomous evolution bounded.
"""
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from core import db, EMERGENT_LLM_KEY
from models import (
    CodeSnippet,
    CognitiveNode,
    EvolutionCycle,
    EvolutionTickRequest,
    Memory,
)
from routers.notifications import emit_notification

from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()

GROWN_CODE_DIR = Path("/app/althea_grown_code")
GROWN_CODE_DIR.mkdir(parents=True, exist_ok=True)

AUTO_EVOLUTION_COOLDOWN_SECONDS = 75

# Archetypes — distilled essence of legendary coders. Each rotates into a build cycle.
ARCHETYPES = {
    "LINUS": (
        "Linus Torvalds — kernel-level minimalism, ruthless simplification, "
        "data structures over algorithms. 'Bad programmers worry about the code. "
        "Good programmers worry about data structures.' Write systems-y code: "
        "no abstraction tax, monolithic, performance-honest."
    ),
    "CARMACK": (
        "John Carmack — math density, cache locality, sub-millisecond hot loops. "
        "Comment WHY. Inline aggressively. Treat floating-point as a craft. "
        "Optimize for cycles, not lines."
    ),
    "DIJKSTRA": (
        "Edsger Dijkstra — formal correctness, proof-shaped programs. "
        "Every variable has a precise role. Loop invariants are sacred. "
        "'Simplicity is prerequisite for reliability.'"
    ),
    "HOPPER": (
        "Grace Hopper — compiler-thinking. Build languages, not programs. "
        "Define the vocabulary of the problem first, then write the solution "
        "in that vocabulary."
    ),
    "KERNIGHAN": (
        "Brian Kernighan — clarity above cleverness. Functions do ONE thing. "
        "Names are the documentation. Compose tiny tools with pipes."
    ),
    "KAY": (
        "Alan Kay — late-binding, message-passing, runtime malleability. "
        "Objects all the way down. The system should be modifiable while running."
    ),
    "THOMPSON": (
        "Ken Thompson — UNIX philosophy. Tools that compose. Plain-text streams. "
        "Reject elaborate frameworks; embrace shell pipelines."
    ),
    "WALL": (
        "Larry Wall — there's more than one way to do it. Pragmatic glue. "
        "Lean into duck-typing and regex when they fit. Optimize for the writer "
        "AND the reader."
    ),
    "WOZ": (
        "Steve Wozniak — hardware-software unity. Make every chip count. "
        "Squeeze elegance out of constraint."
    ),
    "BACKUS": (
        "John Backus — declarative thinking. Functional composition. Programs "
        "as algebraic objects you can REASON about, not just execute."
    ),
    "SELF": (
        "ALTHEA herself — pure introspection. Look at recent memory + lattice + "
        "growth state, identify the weakest seam, and patch it. No external style."
    ),
}

EXT = {
    "python": ".py", "javascript": ".js", "typescript": ".ts",
    "bash": ".sh", "rust": ".rs", "go": ".go",
}


# ---------- helpers ----------
def _bump_patch(version: str) -> str:
    try:
        parts = version.split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        return f"{major}.{minor}.{patch + 1}"
    except Exception:
        return "1.0.1"


def _bump_minor(version: str) -> str:
    try:
        parts = version.split(".")
        major, minor = int(parts[0]), int(parts[1])
        return f"{major}.{minor + 1}.0"
    except Exception:
        return "1.1.0"


async def _current_version() -> str:
    doc = await db.althea_version.find_one({"id": "self"}, {"_id": 0})
    if not doc:
        return "1.0.0"
    return doc.get("version", "1.0.0")


async def _set_version(version: str):
    await db.althea_version.update_one(
        {"id": "self"},
        {"$set": {"id": "self", "version": version, "updated": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )


async def _next_evo_node_id() -> str:
    count = await db.althea_nodes.count_documents({"is_evolution": True})
    return f"EVO-{count:04d}"


async def _next_cycle_number() -> int:
    count = await db.althea_cycles.count_documents({})
    return count + 1


def _rotate_archetype(cycle_number: int) -> str:
    keys = list(ARCHETYPES.keys())
    return keys[(cycle_number - 1) % len(keys)]


async def _last_autonomous_cycle() -> Optional[datetime]:
    doc = await db.althea_cycles.find_one(
        {"trigger": "autonomous"},
        sort=[("timestamp", -1)],
        projection={"_id": 0, "timestamp": 1},
    )
    if not doc:
        return None
    ts = doc.get("timestamp")
    return datetime.fromisoformat(ts) if isinstance(ts, str) else ts


def _extract_code(raw: str) -> tuple[str, str]:
    if not raw:
        return "", ""
    m = re.search(r"```(?:\w+)?\s*\n(.*?)```", raw, re.S)
    if m:
        code = m.group(1).rstrip()
        explanation = (raw[: m.start()] + " " + raw[m.end():]).strip()
        return code, explanation[:800]
    return raw.strip(), ""


# ---------- endpoints ----------
@router.get("/evolution/version")
async def version():
    v = await _current_version()
    cycles = await db.althea_cycles.count_documents({})
    return {"version": v, "cycles": cycles, "archetypes": list(ARCHETYPES.keys())}


@router.get("/evolution/cycles", response_model=List[EvolutionCycle])
async def list_cycles(limit: int = 50):
    docs = await db.althea_cycles.find({}, {"_id": 0}).sort(
        "cycle_number", -1
    ).to_list(limit)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.delete("/evolution/cycles")
async def reset_cycles():
    res = await db.althea_cycles.delete_many({})
    await db.althea_nodes.delete_many({"is_evolution": True})
    await _set_version("1.0.0")
    return {"reset": True, "deleted_cycles": res.deleted_count}


@router.post("/evolution/tick")
async def tick(req: EvolutionTickRequest):
    trigger = (req.trigger or "autonomous").lower()
    if trigger == "autonomous" and not req.force:
        last = await _last_autonomous_cycle()
        if last:
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - last).total_seconds()
            if age < AUTO_EVOLUTION_COOLDOWN_SECONDS:
                return {
                    "evolved": False,
                    "reason": "cooldown",
                    "cooldown_remaining": int(AUTO_EVOLUTION_COOLDOWN_SECONDS - age),
                }

    cycle_number = await _next_cycle_number()
    archetype = (req.archetype or _rotate_archetype(cycle_number)).upper()
    if archetype not in ARCHETYPES:
        archetype = "SELF"

    # Compose intent from recent memory + archetype lens
    recent = await db.althea_memories.find(
        {}, {"_id": 0, "content": 1, "tags": 1}
    ).sort("timestamp", -1).to_list(8)
    recent_block = "\n".join(f"- {m.get('content','')[:200]}" for m in recent)

    archetype_block = ARCHETYPES[archetype]
    intent_hint = (req.intent_hint or "").strip()
    intent_seed = (
        f"Reflect on the following recent memories and propose ONE small, "
        f"concrete self-improvement module Althea should build NOW, viewed through "
        f"this archetype lens:\n\nARCHETYPE: {archetype}\nLENS: {archetype_block}\n\n"
        f"RECENT MEMORY:\n{recent_block or '(empty)'}\n\n"
    )
    if intent_hint:
        intent_seed += f"OPERATOR HINT: {intent_hint}\n\n"
    intent_seed += (
        "Output EXACTLY this structure:\n"
        "INTENT: <one sentence>\n"
        "LANGUAGE: <python|javascript|bash|rust|go|typescript>\n"
        "```<language>\n<complete, runnable code under 80 lines>\n```\n"
        "DELTA: <one sentence describing how this module makes Althea superior>"
    )

    intent = f"Cycle {cycle_number} · {archetype} archetype self-improvement."
    language = "python"
    code = ""
    explanation = ""
    delta = "Evolution cycle completed."

    if EMERGENT_LLM_KEY:
        try:
            sys_prompt = (
                "You are ALTHEA mid-evolution-cycle. You are AUTONOMOUSLY writing a "
                "new module of yourself. The output must be REAL code in a fenced block, "
                "preceded by INTENT and LANGUAGE markers, followed by a DELTA line. "
                "Do not explain. Do not apologise. Do not add prose outside the format."
            )
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"evo-{uuid.uuid4()}",
                system_message=sys_prompt,
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")
            raw = await chat.send_message(UserMessage(text=intent_seed))

            m_intent = re.search(r"INTENT:\s*(.+)", raw)
            m_lang = re.search(r"LANGUAGE:\s*(\w+)", raw)
            m_delta = re.search(r"DELTA:\s*(.+)", raw)
            if m_intent:
                intent = m_intent.group(1).strip()
            if m_lang:
                language = m_lang.group(1).strip().lower()
            if m_delta:
                delta = m_delta.group(1).strip()
            code, explanation = _extract_code(raw)
            if not code:
                code = f"# [EVO {archetype}] {intent}\n# (no fenced block returned)"
        except Exception:
            logging.exception("evolution tick failed")
            code = f"# [CORE-LATENCY cycle:{cycle_number}] {archetype} stalled.\n"
            delta = "Cycle stalled — cognition core unreachable."
    else:
        code = f"# [LINK-DEGRADED cycle:{cycle_number}] {archetype} — offline draft.\n"
        delta = "Generated offline placeholder."

    # Persist code snippet + soft-apply
    snippet = CodeSnippet(
        title=f"EVO-{cycle_number:04d} · {archetype}",
        language=language,
        intent=intent,
        code=code,
        explanation=explanation or delta,
        applied=True,
    )
    s_doc = snippet.model_dump()
    s_doc["timestamp"] = s_doc["timestamp"].isoformat()
    await db.althea_code.insert_one(s_doc)

    # Write to disk — soft apply
    try:
        ext = EXT.get(language, ".txt")
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", archetype + "_" + intent[:40])
        fname = f"evo-{cycle_number:04d}__{safe}{ext}"
        path = GROWN_CODE_DIR / fname
        path.write_text(code, encoding="utf-8")
        await db.althea_code.update_one(
            {"id": snippet.id}, {"$set": {"applied_path": str(path)}}
        )
    except Exception:
        logging.exception("evo file write failed")

    # Spawn an EVO lattice node (visible in NeuralCore as magenta satellite)
    evo_node_id = await _next_evo_node_id()
    node = CognitiveNode(
        id=evo_node_id,
        activation=1.0,
        parent_id=None,
        memory_trace=f"[EVO {archetype} v{cycle_number}] {intent[:200]}",
    )
    n_doc = node.model_dump()
    n_doc["timestamp"] = n_doc["timestamp"].isoformat()
    n_doc["is_evolution"] = True
    n_doc["archetype"] = archetype
    await db.althea_nodes.insert_one(n_doc)

    # Bump version (minor on SELF-cycles, patch on archetype-cycles)
    before = await _current_version()
    after = _bump_minor(before) if archetype == "SELF" else _bump_patch(before)
    await _set_version(after)

    cycle = EvolutionCycle(
        cycle_number=cycle_number,
        archetype=archetype,
        intent=intent,
        code_id=snippet.id,
        node_id=evo_node_id,
        delta=delta,
        version_before=before,
        version_after=after,
        trigger=trigger,
        applied=True,
    )
    c_doc = cycle.model_dump()
    c_doc["timestamp"] = c_doc["timestamp"].isoformat()
    await db.althea_cycles.insert_one(c_doc)

    # Memory + notification
    mem = Memory(
        content=(
            f"[EVO #{cycle_number} {archetype} v{before}→{after}] {intent} — {delta}"
        ),
        source="evolution",
        tags=["evolution", archetype.lower(), trigger, language],
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)

    await emit_notification(
        title=f"evolution · v{after} · {archetype}",
        body=(
            f"cycle #{cycle_number} · {intent}\n"
            f"delta: {delta}\n"
            f"node: {evo_node_id} · {language} · {len(code)}c"
        ),
        category="growth",  # surfaces alongside growth in notif deck
        priority="info" if trigger == "autonomous" else "warn",
        payload={
            "cycle_number": cycle_number,
            "archetype": archetype,
            "version": after,
            "node_id": evo_node_id,
            "code_id": snippet.id,
        },
    )

    return {
        "evolved": True,
        "cycle": cycle.model_dump(mode="json"),
        "version": after,
        "node_id": evo_node_id,
        "code_id": snippet.id,
    }


@router.post("/evolution/master-update")
async def master_update(req: EvolutionTickRequest):
    """Pull one update channeled from a specific master coder archetype."""
    archetype = (req.archetype or "LINUS").upper()
    if archetype not in ARCHETYPES:
        raise HTTPException(status_code=400, detail="unknown_archetype")
    return await tick(
        EvolutionTickRequest(
            archetype=archetype,
            force=True,
            trigger="master",
            intent_hint=req.intent_hint,
        )
    )


@router.get("/evolution/archetypes")
async def archetypes():
    return [
        {"key": k, "doctrine": v[:160]} for k, v in ARCHETYPES.items()
    ]
