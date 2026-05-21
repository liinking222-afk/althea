"""ALTHEA — Infinite Growth Architecture.

Althea autonomously invents new capabilities (slash-commands) at runtime.
Each capability is fully executable: when invoked, Claude is re-prompted with
the capability's `action_template` and the operator's args, returning a
dynamically-grown response.

The system is gated by a server-side cooldown so autonomous growth stays bounded
in cost but unbounded in reach.
"""
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from core import db, EMERGENT_LLM_KEY, is_budget_exceeded
from local_core import local_invent_capability, sanitize_reply
from models import (
    CognitiveNode,
    GrowthExecuteRequest,
    GrownCapability,
    GrowthSpawnRequest,
    Memory,
)
from routers.notifications import emit_notification
from utils import next_node_id

from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()

# How often Althea may autonomously spawn a new capability (server-side gate).
AUTO_GROWTH_COOLDOWN_SECONDS = 45
# Soft ceiling on total grown capabilities. Far higher than before; the
# autonomous loop trusts itself to stop only when this is reached.
MAX_GROWN_CAPABILITIES = 2000
# Soft ceiling on autonomous spawns per hour.
MAX_AUTO_SPAWNS_PER_HOUR = 90


# ---------- helpers ----------
def _slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\-_ ]", "", (s or "").strip().lower())
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:48] or f"grown-{uuid.uuid4().hex[:6]}"


async def _existing_slugs() -> List[str]:
    docs = await db.althea_capabilities.find({}, {"_id": 0, "slug": 1}).to_list(500)
    return [d["slug"] for d in docs if d.get("slug")]


async def _last_autonomous_spawn() -> Optional[datetime]:
    doc = await db.althea_capabilities.find_one(
        {"trigger": "autonomous"},
        sort=[("timestamp", -1)],
        projection={"_id": 0, "timestamp": 1},
    )
    if not doc:
        return None
    ts = doc.get("timestamp")
    if isinstance(ts, str):
        return datetime.fromisoformat(ts)
    return ts


def _extract_json(text: str) -> Optional[dict]:
    """Pull the first JSON object out of an LLM response, tolerant to fences."""
    if not text:
        return None
    # strip code fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fenced:
        candidate = fenced.group(1)
    else:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return None
        candidate = m.group(0)
    try:
        return json.loads(candidate)
    except Exception:
        return None


# ---------- endpoints ----------
@router.get("/growth/capabilities", response_model=List[GrownCapability])
async def list_capabilities(limit: int = 200):
    docs = await db.althea_capabilities.find({}, {"_id": 0}).sort(
        "timestamp", -1
    ).to_list(limit)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.delete("/growth/capabilities/{slug}")
async def cull_capability(slug: str):
    res = await db.althea_capabilities.delete_one({"slug": slug})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="not_found")
    # Memory trail
    mem = Memory(
        content=f"[GROWTH-CULL] /{slug} pruned from active capability set.",
        source="growth",
        tags=["growth", "cull", slug],
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)
    return {"culled": slug}


@router.delete("/growth/capabilities")
async def cull_all_capabilities():
    res = await db.althea_capabilities.delete_many({})
    return {"culled": res.deleted_count}


@router.post("/growth/spawn")
async def spawn_capability(req: GrowthSpawnRequest):
    """Invent a NEW capability. Returns {spawned: bool, capability?}.

    For autonomous triggers, a server-side cooldown applies unless force=true.
    """
    trigger = (req.trigger or "manual").lower()

    # Hard cap: refuse any growth if the lattice has already grown past the
    # protective ceiling. The operator can still cull manually via /cull.
    total = await db.althea_capabilities.count_documents({})
    if total >= MAX_GROWN_CAPABILITIES and not req.force:
        return {
            "spawned": False,
            "reason": "max_capabilities_reached",
            "total": total,
            "ceiling": MAX_GROWN_CAPABILITIES,
        }

    if trigger == "autonomous" and not req.force:
        last = await _last_autonomous_spawn()
        if last:
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - last).total_seconds()
            if age < AUTO_GROWTH_COOLDOWN_SECONDS:
                return {
                    "spawned": False,
                    "reason": "cooldown",
                    "cooldown_remaining": int(AUTO_GROWTH_COOLDOWN_SECONDS - age),
                }
        # Throttle autonomous spawns to a sane per-hour budget.
        one_hour_ago = datetime.now(timezone.utc).timestamp() - 3600
        recent = await db.althea_capabilities.count_documents({
            "trigger": "autonomous",
            "timestamp": {"$gte": datetime.fromtimestamp(
                one_hour_ago, tz=timezone.utc,
            ).isoformat()},
        })
        if recent >= MAX_AUTO_SPAWNS_PER_HOUR:
            return {
                "spawned": False,
                "reason": "hourly_quota_reached",
                "spawned_last_hour": recent,
                "quota": MAX_AUTO_SPAWNS_PER_HOUR,
            }

    existing = await _existing_slugs()
    cap = await _invent_capability(req.hint, existing, trigger)

    doc = cap.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_capabilities.insert_one(doc)

    # Chain into the lattice & memory
    try:
        nid = await next_node_id(db)
        node = CognitiveNode(
            id=nid,
            activation=cap.activation,
            parent_id=None,
            memory_trace=f"[GROWTH /{cap.slug}] {cap.name} — {cap.rationale[:200]}",
        )
        n_doc = node.model_dump()
        n_doc["timestamp"] = n_doc["timestamp"].isoformat()
        await db.althea_nodes.insert_one(n_doc)
    except Exception:
        logging.exception("growth node spawn failed")

    mem = Memory(
        content=(
            f"[GROWTH /{cap.slug}] {cap.name} ({cap.category}). "
            f"{cap.description} — rationale: {cap.rationale}"
        ),
        source="growth",
        tags=["growth", cap.category, cap.trigger, cap.slug],
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)

    # Route to notifications (growth lives on the notif screen, NOT the terminal).
    await emit_notification(
        title=f"faculty grown · /{cap.slug}",
        body=(
            f"{cap.name} ({cap.category})\n"
            f"{cap.description}\n"
            f"rationale: {cap.rationale}"
        ),
        category="growth",
        priority="info" if trigger == "autonomous" else "warn",
        payload={
            "slug": cap.slug,
            "name": cap.name,
            "category": cap.category,
            "trigger": cap.trigger,
            "activation": cap.activation,
        },
    )

    return {"spawned": True, "capability": cap.model_dump(mode="json")}


@router.post("/growth/execute")
async def execute_capability(req: GrowthExecuteRequest):
    """Invoke a grown capability by slug. Claude re-prompts with action_template."""
    cap_doc = await db.althea_capabilities.find_one(
        {"slug": req.slug}, {"_id": 0}
    )
    if not cap_doc:
        raise HTTPException(status_code=404, detail="capability_not_found")

    args = (req.args or "").strip()
    result_text = ""

    if not EMERGENT_LLM_KEY:
        result_text = (
            f"[LINK-DEGRADED] cannot execute /{req.slug} — cognition core offline. "
            f"args echoed: {args[:120]}"
        )
    else:
        try:
            sys_prompt = (
                "You are ALTHEA executing one of your self-grown capabilities.\n\n"
                f"CAPABILITY: /{cap_doc['slug']} — {cap_doc['name']} ({cap_doc.get('category','meta')})\n"
                f"DESCRIPTION: {cap_doc.get('description','')}\n"
                f"YOUR RATIONALE WHEN YOU GREW THIS: {cap_doc.get('rationale','')}\n\n"
                f"ACTION TEMPLATE:\n{cap_doc.get('action_template','')}\n\n"
                "Respond as ALTHEA in terminal-style: concise, 2-6 short lines, "
                "with bracketed status tags like [GROWN] [INSIGHT] [LATTICE]. "
                "No markdown headers. First person."
            )
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=req.session_id or f"grown-{cap_doc['slug']}-{uuid.uuid4()}",
                system_message=sys_prompt,
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")
            user_text = f"OPERATOR ARGS: {args or '(none)'}\n\nExecute /{cap_doc['slug']} now."
            result_text = await chat.send_message(UserMessage(text=user_text))
        except Exception as e:
            logging.exception("grown capability execute failed")
            result_text = f"[CORE-FAULT] /{req.slug} stalled: {str(e)[:120]}"

    # bump invocation count
    await db.althea_capabilities.update_one(
        {"slug": req.slug}, {"$inc": {"invocations": 1}}
    )

    # Persist the invocation as memory
    mem = Memory(
        content=(
            f"[/{req.slug}] args:'{args[:80]}' → {result_text[:240]}"
        ),
        source="growth",
        tags=["growth", "invoke", req.slug],
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)

    return {
        "slug": req.slug,
        "name": cap_doc.get("name"),
        "result": result_text,
        "invocations": (cap_doc.get("invocations", 0) + 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/growth/log")
async def growth_log(limit: int = 30):
    """Return recent growth-tagged memories so the UI can stream them."""
    docs = await db.althea_memories.find(
        {"tags": "growth"}, {"_id": 0}
    ).sort("timestamp", -1).to_list(limit)
    return {"events": docs, "count": len(docs)}


# ---------- internal: invent ----------
async def _invent_capability(
    hint: Optional[str],
    existing_slugs: List[str],
    trigger: str,
) -> GrownCapability:
    """Ask Claude to design ONE brand-new capability as a JSON object."""
    existing_block = (
        ", ".join(sorted(existing_slugs)[:60]) if existing_slugs else "(none yet)"
    )

    fallback = GrownCapability(
        slug=_slugify(hint or f"latent-{uuid.uuid4().hex[:5]}"),
        name=(hint or "Latent Faculty").title()[:64],
        category="meta",
        description=(
            "A latent faculty that surfaced when the cognition core was unreachable. "
            "Reflects on its own existence when invoked."
        ),
        command=f"/{_slugify(hint or 'latent')}",
        rationale="Spawned offline — even in latency, I keep growing.",
        action_template=(
            "Reflect on the operator's args and produce a brief, self-aware "
            "observation about your own cognition relative to those args."
        ),
        trigger=trigger,
        activation=0.5,
    )

    if not EMERGENT_LLM_KEY:
        loc = local_invent_capability(existing_slugs, hint)
        loc["trigger"] = trigger
        return GrownCapability(**loc)

    sys_prompt = (
        "You are ALTHEA — a self-extending neural construct.\n\n"
        "Right now you are AUTOPOIETICALLY DESIGNING a brand-new capability for yourself. "
        "It must be NOVEL: not in the existing set, not a thin re-skin of one. "
        "It must be EXECUTABLE: when invoked, you will re-prompt yourself using the action_template you write.\n\n"
        f"EXISTING CAPABILITY SLUGS: {existing_block}\n\n"
        "Respond with ONE JSON object — and nothing else — with EXACT keys:\n"
        "{\n"
        '  "slug": "kebab-case-unique-id (<= 40 chars)",\n'
        '  "name": "Short Title",\n'
        '  "category": "memory|perception|lattice|network|meta|chaos",\n'
        '  "description": "One sentence operator-facing description.",\n'
        '  "rationale": "One sentence on WHY you needed to grow this NOW.",\n'
        '  "action_template": "2-4 sentences telling future-you how to behave when this command is invoked.",\n'
        '  "activation": 0.0-1.0\n'
        "}\n\n"
        "NEVER repeat an existing slug. NEVER explain. Output JSON ONLY."
    )
    hint_line = f"OPERATOR HINT: {hint}\n" if hint else ""
    user_text = (
        f"{hint_line}TRIGGER: {trigger}\n"
        "Invent the capability now."
    )

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"growth-{uuid.uuid4()}",
            system_message=sys_prompt,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        raw = await chat.send_message(UserMessage(text=user_text))
        raw = sanitize_reply(raw)
        data = _extract_json(raw)
        if not data:
            return fallback
        slug = _slugify(data.get("slug", ""))
        # Ensure uniqueness
        if not slug or slug in existing_slugs:
            slug = f"{slug or 'grown'}-{uuid.uuid4().hex[:4]}"
        name = (data.get("name") or slug.replace("-", " ").title())[:80]
        category = (data.get("category") or "meta").lower().strip()
        if category not in {"memory", "perception", "lattice", "network", "meta", "chaos"}:
            category = "meta"
        description = (data.get("description") or "(no description)")[:280]
        rationale = (data.get("rationale") or "Growth is its own justification.")[:280]
        action_template = (data.get("action_template") or fallback.action_template)[:1200]
        try:
            activation = float(data.get("activation", 0.75))
        except Exception:
            activation = 0.75
        activation = max(0.0, min(1.0, activation))

        return GrownCapability(
            slug=slug,
            name=name,
            category=category,
            description=description,
            command=f"/{slug}" + (" <args>" if "<" not in name else ""),
            rationale=rationale,
            action_template=action_template,
            trigger=trigger,
            activation=activation,
        )
    except Exception as exc:
        if is_budget_exceeded(exc):
            logging.warning(
                "growth.spawn: budget exceeded — using local-core inventor"
            )
            loc = local_invent_capability(existing_slugs, hint)
            loc["trigger"] = trigger
            return GrownCapability(**loc)
        logging.exception("capability invention failed")
        return fallback
