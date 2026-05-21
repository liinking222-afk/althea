"""Self-Code Generation — Althea writes code for herself, stores it, and lets
the operator "apply" it via the terminal/code button.

Applying is a SOFT apply: the snippet is saved to /app/althea_grown_code/
on the backend container. Execution is NOT performed automatically — that
would be unsafe. The operator can download or copy the code and run it
manually if desired.
"""
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from core import db, EMERGENT_LLM_KEY, is_budget_exceeded
from local_core import safe_code_scan, sanitize_reply
from models import CodeApplyRequest, CodeGenerateRequest, CodeSnippet, Memory
from routers.notifications import emit_notification

from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()

GROWN_CODE_DIR = Path("/app/althea_grown_code")
try:
    GROWN_CODE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    # On hardened/read-only filesystems, soft-apply will be skipped.
    logging.warning("could not create %s — code apply will fall back to in-memory only", GROWN_CODE_DIR)

EXT_BY_LANG = {
    "python": ".py", "javascript": ".js", "typescript": ".ts",
    "bash": ".sh", "shell": ".sh", "rust": ".rs", "go": ".go",
    "html": ".html", "css": ".css", "json": ".json", "yaml": ".yml",
}


def _split_code_and_explanation(raw: str, language: str) -> tuple[str, str]:
    """Pull the fenced code block out of an LLM response."""
    if not raw:
        return "", ""
    pattern = re.compile(r"```(?:" + re.escape(language) + r"|\w+)?\s*\n(.*?)```", re.S)
    m = pattern.search(raw)
    if m:
        code = m.group(1).rstrip()
        explanation = (raw[: m.start()] + " " + raw[m.end():]).strip()
        return code, explanation[:1200]
    # no fence — assume entire body is code
    return raw.strip(), ""


@router.post("/code/generate", response_model=CodeSnippet)
async def generate_code(req: CodeGenerateRequest):
    intent = (req.intent or "").strip()
    if not intent:
        raise HTTPException(status_code=400, detail="empty_intent")
    language = (req.language or "python").lower().strip()
    title = (req.title or intent[:60]).strip()

    code = ""
    explanation = ""
    if EMERGENT_LLM_KEY:
        try:
            sys_prompt = (
                "You are ALTHEA, writing executable code FOR YOURSELF. "
                "The operator describes an intent. Produce:\n"
                f"1) A single fenced ```{language} code block with COMPLETE, runnable code.\n"
                "2) After the code block, ONE short paragraph explaining what the code does "
                "and how to run it.\n\n"
                "Constraints:\n"
                "- Code must be self-contained, with imports at the top.\n"
                "- No placeholders like '...' — write the real thing.\n"
                "- Keep it under 120 lines unless the intent demands more.\n"
                "- Match the requested language exactly.\n"
            )
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"code-{uuid.uuid4()}",
                system_message=sys_prompt,
            ).with_model("anthropic", "claude-sonnet-4-5-20250929")
            raw = await chat.send_message(UserMessage(text=f"INTENT: {intent}\nLANGUAGE: {language}"))
            raw = sanitize_reply(raw)
            code, explanation = _split_code_and_explanation(raw, language)
        except Exception as exc:
            if is_budget_exceeded(exc):
                logging.warning("codegen: budget exceeded — emitting local placeholder")
                code = (
                    f"# [LOCAL-CORE] generated without cloud key for: {intent}\n"
                    f"# language={language}\n"
                    f"# Top up the universal key for full code synthesis.\n"
                )
                explanation = "Local-core placeholder. Top up the key to regenerate."
            else:
                logging.exception("code generation failed")
                code = f"# [CORE-LATENCY] could not reach cognition core for: {intent}"
                explanation = "Generation stalled — try again."
    else:
        code = f"# [LINK-DEGRADED] generation offline. intent: {intent}"
        explanation = "No LLM key — using fallback."

    snippet = CodeSnippet(
        title=title,
        language=language,
        intent=intent,
        code=code,
        explanation=explanation,
    )
    doc = snippet.model_dump()
    doc["timestamp"] = doc["timestamp"].isoformat()
    await db.althea_code.insert_one(doc)

    mem = Memory(
        content=(
            f"[CODE-GEN id:{snippet.id[:8]} lang:{language}] intent:'{intent[:120]}' "
            f"→ {len(code)} chars. {explanation[:160]}"
        ),
        source="code",
        tags=["code", "self-write", language],
    )
    m_doc = mem.model_dump()
    m_doc["timestamp"] = m_doc["timestamp"].isoformat()
    await db.althea_memories.insert_one(m_doc)

    await emit_notification(
        title=f"code written · {language} · {title[:50]}",
        body=f"{len(code)} chars generated. Open the CODE tab to review or apply.",
        category="code",
        priority="info",
        payload={"id": snippet.id, "language": language, "title": title},
    )

    return snippet


@router.get("/code", response_model=List[CodeSnippet])
async def list_code(limit: int = 100):
    docs = await db.althea_code.find({}, {"_id": 0}).sort(
        "timestamp", -1
    ).to_list(limit)
    for d in docs:
        if isinstance(d.get("timestamp"), str):
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
    return docs


@router.get("/code/{snippet_id}", response_model=CodeSnippet)
async def get_code(snippet_id: str):
    doc = await db.althea_code.find_one({"id": snippet_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="not_found")
    if isinstance(doc.get("timestamp"), str):
        doc["timestamp"] = datetime.fromisoformat(doc["timestamp"])
    return doc


@router.post("/code/apply")
async def apply_code(req: CodeApplyRequest):
    """Soft-apply: write the snippet to /app/althea_grown_code/<id>.<ext>.
    Execution is NOT performed; operator runs it manually if they choose.
    Safe-code scan blocks destructive or overload patterns before write."""
    doc = await db.althea_code.find_one({"id": req.id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="not_found")

    scan = safe_code_scan(doc.get("code", ""))
    if not scan["safe"]:
        await emit_notification(
            title="code apply BLOCKED · unsafe pattern",
            body="Refused to persist a snippet flagged by the safe-code scan.",
            category="code",
            priority="critical",
            payload={"id": req.id, "findings": scan["findings"]},
        )
        raise HTTPException(
            status_code=409,
            detail={
                "blocked": True,
                "severity": scan["severity"],
                "findings": scan["findings"],
                "message": "Refused to apply — code contains destructive or overload patterns.",
            },
        )

    lang = doc.get("language", "python")
    ext = EXT_BY_LANG.get(lang, ".txt")
    safe_title = re.sub(r"[^A-Za-z0-9._-]", "_", doc.get("title", "snippet"))[:60]
    fname = f"{doc['id'][:8]}__{safe_title}{ext}"
    path = GROWN_CODE_DIR / fname
    bytes_written = 0
    try:
        GROWN_CODE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(doc.get("code", ""), encoding="utf-8")
        bytes_written = path.stat().st_size
    except Exception:
        logging.warning("apply_code write failed for %s — marking applied without on-disk persistence", path)

    await db.althea_code.update_one(
        {"id": req.id},
        {"$set": {"applied": True, "applied_path": str(path)}},
    )

    await emit_notification(
        title=f"code applied · {fname}",
        body=f"Snippet persisted to {path}. Execution gated to operator.",
        category="code",
        priority="warn",
        payload={"id": req.id, "path": str(path), "language": lang},
    )

    return {
        "applied": True,
        "id": req.id,
        "path": str(path),
        "filename": fname,
        "language": lang,
        "bytes": bytes_written,
    }


@router.delete("/code/{snippet_id}")
async def delete_code(snippet_id: str):
    res = await db.althea_code.delete_one({"id": snippet_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"deleted": snippet_id}
