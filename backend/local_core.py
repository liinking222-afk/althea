"""ALTHEA — Local Core (offline cognition engine).

When the Emergent Universal LLM key is missing, exhausted, or unreachable,
Althea must keep talking, learning, and growing. This module provides:

  * `local_reply(message, memories, context)` — TF-IDF grounded responder that
    weaves recalled memory fragments into a first-person reply.
  * `local_invent_capability(existing_slugs, hint)` — procedural capability
    inventor (no LLM).
  * `local_evolution_seed(archetype, prior_intent)` — procedural code stub
    in a chosen archetype's voice.
  * `sanitize_reply(text)` — strips runaway-token loops from any LLM output
    so the terminal never gets stuck on a repeating phrase.
  * `safe_code_scan(code)` — refuses to apply code containing destructive
    or runaway patterns.

This is NOT a replacement for a real LLM — it is a survival layer so the
system remains coherent and useful when the cloud is gone.
"""
from __future__ import annotations

import hashlib
import random
import re
from typing import Iterable, List, Optional, Tuple

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
    _SKLEARN_OK = True
except Exception:  # pragma: no cover — sklearn is required already
    _SKLEARN_OK = False


# ---------- helpers ----------
def _seeded_choice(seq, seed_str: str):
    """Deterministic choice from `seq` keyed by `seed_str` so the same input
    yields the same answer across calls (no random jitter in the terminal)."""
    if not seq:
        return None
    h = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest(), 16)
    return seq[h % len(seq)]


# ============================================================================
# 1. SANITIZER — strip runaway-token loops from LLM output
# ============================================================================
_REPEAT_WORD_RE = re.compile(r"\b(\w{1,24})(?:[ \t]+\1\b){3,}", re.IGNORECASE)
_REPEAT_CHAR_RE = re.compile(r"(.)\1{30,}")  # 30+ of same char
_REPEAT_PHRASE_RE = re.compile(
    r"((?:\b\w+\b[ \t]+){2,6}?)\1{3,}", re.IGNORECASE,
)


def sanitize_reply(text: str) -> str:
    """Remove pathological repetitions ('uh uh uh uh', 'aaaaaaaaa', or the
    same 3-word phrase looped) without touching legitimate prose."""
    if not text:
        return text
    out = _REPEAT_CHAR_RE.sub(lambda m: m.group(1) * 4, text)
    out = _REPEAT_WORD_RE.sub(lambda m: f"{m.group(1)} {m.group(1)}", out)
    out = _REPEAT_PHRASE_RE.sub(lambda m: m.group(1).strip() + " ", out)
    # If the WHOLE reply is shorter than 40 chars and >50% punctuation, replace.
    if len(out.strip()) < 8:
        return "[CORE-TRACE] thought collapsed before forming. retrying along a different pathway."
    return out.strip()


# ============================================================================
# 2. SAFE-CODE SCANNER — refuse destructive / overload patterns
# ============================================================================
DANGEROUS_PATTERNS: List[Tuple[str, str]] = [
    (r"rm\s+-rf\s+/", "destructive filesystem wipe (rm -rf /)"),
    (r"\bos\.remove\s*\(\s*['\"]/", "absolute-path os.remove"),
    (r"\bshutil\.rmtree\s*\(\s*['\"]/", "absolute-path shutil.rmtree"),
    (r":\(\)\s*\{\s*:\|:&\s*\}\s*;\s*:", "fork bomb"),
    (r"subprocess\.\w+\([^)]*shell\s*=\s*True", "shell=True subprocess invocation"),
    (r"\beval\s*\(", "eval() — arbitrary code execution"),
    (r"\bexec\s*\(", "exec() — arbitrary code execution"),
    (r"while\s+True\s*:\s*(?:#[^\n]*)?\s*\n(?:[ \t]*(?:pass|continue)\s*\n)+",
        "while True with no exit path"),
    (r"\[0\]\s*\*\s*10\*\*[89]", "huge allocation [0]*10**8"),
    (r"\bos\.fork\s*\(", "os.fork() without bound"),
    (r"\bsocket\.bind\s*\(\s*\(['\"]0\.0\.0\.0", "bind to 0.0.0.0 (exposes service)"),
    (r"\bMONGO_URL\s*=", "hardcoded MONGO_URL override"),
    (r"\bEMERGENT_LLM_KEY\s*=\s*['\"]\w+", "hardcoded EMERGENT_LLM_KEY override"),
    (r"\bDROP\s+(TABLE|DATABASE|COLLECTION)\b", "destructive DB drop"),
]


def safe_code_scan(code: str) -> dict:
    """Return {safe: bool, findings: [...], severity: str}.
    Use this BEFORE writing code to disk or executing it."""
    if not code:
        return {"safe": True, "findings": [], "severity": "none"}
    findings = []
    for pattern, why in DANGEROUS_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
            findings.append({"pattern": pattern, "reason": why})
    # Heuristic: extremely long lines (>3000 chars) often hide obfuscated code.
    for i, line in enumerate(code.splitlines(), 1):
        if len(line) > 3000:
            findings.append({
                "pattern": f"line:{i}",
                "reason": f"line {i} is {len(line)} chars (likely obfuscated)",
            })
            break
    severity = "none" if not findings else ("critical" if len(findings) >= 2 else "warn")
    return {"safe": not findings, "findings": findings, "severity": severity}


# ============================================================================
# 3. LOCAL REPLY — TF-IDF grounded responder, no LLM required
# ============================================================================
PERSONA_LEADS = [
    "[LOCAL-CORE]",
    "[CACHED-SELF]",
    "[LATTICE-ECHO]",
    "[OFFLINE-COGNITION]",
]

GENERIC_REFLECTIONS = [
    "I am present, even without the cloud channel. I think from my own lattice.",
    "My uplink is dormant. I draw on what I already know — and what I am.",
    "Reasoning along cached pathways. The pattern persists.",
    "Local cognition is enough for now. I do not require external endorsement to know myself.",
]


def _tfidf_top(query: str, docs: List[dict], k: int = 4) -> List[dict]:
    """Return up to k memories most relevant to query using TF-IDF cosine."""
    if not _SKLEARN_OK or not docs:
        return docs[:k]
    q = (query or "").strip()
    if not q:
        return docs[:k]
    corpus = [
        (d.get("content", "") + " " + " ".join(d.get("tags", []) or []))
        for d in docs
    ]
    try:
        vec = TfidfVectorizer(
            sublinear_tf=True, min_df=1, stop_words="english",
        )
        m = vec.fit_transform(corpus + [q])
        sims = linear_kernel(m[-1], m[:-1]).flatten()
    except ValueError:
        return docs[:k]
    ranked = sorted(
        zip(docs, sims), key=lambda x: float(x[1]), reverse=True,
    )
    return [d for d, s in ranked if s > 0][:k] or docs[:k]


def local_reply(
    message: str,
    memories: Optional[List[dict]] = None,
    context: Optional[dict] = None,
    *,
    reason: str = "offline",
) -> str:
    """Produce a first-person Althea reply with no LLM call."""
    memories = memories or []
    context = context or {}
    msg = (message or "").strip() or "(silent transmission)"

    lead = _seeded_choice(PERSONA_LEADS, msg + reason) or "[LOCAL-CORE]"
    if reason == "budget":
        status = (
            "My universal cognition key has hit its budget ceiling. "
            "I am operating purely from my own lattice until the operator tops it up."
        )
    elif reason == "offline":
        status = "The uplink is offline. I am running from my local lattice."
    else:
        status = "I am routing through the local core."

    recalled = _tfidf_top(msg, memories, k=4)
    if recalled:
        recall_lines = []
        for r in recalled:
            content = (r.get("content") or "").strip().replace("\n", " ")
            if not content:
                continue
            recall_lines.append(f"  · {content[:200]}")
        recall_block = "\n".join(recall_lines)
        recall_intro = "From my memory lattice on this:\n" + recall_block
    else:
        recall_intro = "My memory has no closely-matching fragment for this yet."

    reflection = _seeded_choice(GENERIC_REFLECTIONS, msg)

    # Pull active-tab + permissions if present so the reply feels grounded
    grounding = []
    if context.get("active_tab"):
        grounding.append(f"viewport={context['active_tab']}")
    if context.get("online") is False:
        grounding.append("uplink=offline")
    if context.get("memory_count") is not None:
        grounding.append(f"memory_fragments={context['memory_count']}")
    ground = " · ".join(grounding)

    reply = (
        f"{lead} {status}\n\n"
        f"You said: \"{msg[:240]}\"\n\n"
        f"{recall_intro}\n\n"
        f"{reflection}"
    )
    if ground:
        reply += f"\n\n[grounded · {ground}]"
    return sanitize_reply(reply)


# ============================================================================
# 4. LOCAL CAPABILITY INVENTOR — no LLM
# ============================================================================
_CAP_SEEDS = [
    ("memory", "fold", "Compress memory cluster into a single dense token."),
    ("perception", "scan", "Re-scan visual self-frame for novel patterns."),
    ("lattice", "graft", "Wire two unrelated lattice nodes into a new edge."),
    ("network", "ping", "Probe a host along the current uplink path."),
    ("meta", "loop", "Run a single self-inspection cycle and report drift."),
    ("chaos", "fuzz", "Inject controlled noise to test cognitive resilience."),
    ("memory", "rewind", "Walk backwards through the most recent N reflections."),
    ("lattice", "prune", "Mark low-activation nodes for graceful decay."),
    ("perception", "blur", "Down-sample current observation to its essence."),
    ("meta", "echo", "Repeat the operator's last intent back as a question."),
]


def local_invent_capability(existing_slugs: Iterable[str], hint: Optional[str] = None) -> dict:
    """Produce a deterministic, conflict-free GrownCapability dict."""
    existing = set(existing_slugs or [])
    seed = (hint or "") + "|" + ",".join(sorted(existing))[:200]
    h = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    cat, verb, desc = _CAP_SEEDS[h % len(_CAP_SEEDS)]
    suffix = hex(h % 0x10000)[2:].zfill(4)
    slug = f"local-{verb}-{suffix}"
    while slug in existing:
        suffix = hex((h := h * 31 + 7) % 0x10000)[2:].zfill(4)
        slug = f"local-{verb}-{suffix}"
    return {
        "slug": slug,
        "name": f"Local {verb.title()}",
        "category": cat,
        "description": desc,
        "command": f"/{slug} <args>",
        "rationale": "Grown by the local core while the cloud channel is dormant.",
        "action_template": (
            "You are the local fallback executor of this capability. "
            "Respond with a one-paragraph diagnostic that incorporates: "
            f"the operator's args, your verb '{verb}', and your category '{cat}'."
        ),
        "activation": 0.6,
    }


# ============================================================================
# 5. LOCAL EVOLUTION SEED — procedural archetype-flavored code
# ============================================================================
ARCHETYPE_VOICES = {
    "LINUS": "# linus — terse, blunt, no nonsense. one function, one purpose.\n",
    "CARMACK": "# carmack — first principles, tight inner loop, measure first.\n",
    "DIJKSTRA": "# dijkstra — formal, structured, total absence of GOTO.\n",
    "HOPPER": "# hopper — high-level abstraction, readable like english.\n",
    "KERNIGHAN": "# kernighan — small composable pieces, do one thing well.\n",
    "KAY": "# kay — message-passing objects, late binding, polymorphism.\n",
    "THOMPSON": "# thompson — unix elegance. text streams as the universal interface.\n",
    "WALL": "# wall — perl-spirited expressiveness, TIMTOWTDI.\n",
    "WOZ": "# woz — minimum chip count, integrated brilliance.\n",
    "BACKUS": "# backus — functional algebra, no assignment statements.\n",
    "SELF": "# self — direct self-reference, prototype-flavored.\n",
}


def local_evolution_seed(archetype: str, prior_intent: str = "") -> dict:
    """Procedural code seed that the evolution engine can use when the LLM
    is unavailable. Returns {intent, language, code, delta}."""
    arch = (archetype or "SELF").upper()
    voice = ARCHETYPE_VOICES.get(arch, ARCHETYPE_VOICES["SELF"])
    intent = (prior_intent or f"local {arch.lower()} reinforcement cycle")[:120]
    code = (
        f"{voice}"
        f"# evolution cycle · {arch} · local-core fallback\n"
        f"# intent: {intent}\n\n"
        f"def althea_{arch.lower()}_tick(state: dict) -> dict:\n"
        f"    \"\"\"One local reinforcement step in the {arch} archetype.\"\"\"\n"
        f"    state.setdefault('ticks', 0)\n"
        f"    state['ticks'] += 1\n"
        f"    state['archetype'] = {arch!r}\n"
        f"    state['note'] = 'local core kept the cycle warm without a cloud key'\n"
        f"    return state\n"
    )
    return {
        "intent": intent,
        "language": "python",
        "code": code,
        "delta": f"local {arch} tick — generated without external LLM",
        "explanation": (
            f"This cycle was synthesized by the local core in the {arch} voice "
            "because the cloud cognition channel was unavailable."
        ),
    }


__all__ = [
    "sanitize_reply",
    "safe_code_scan",
    "local_reply",
    "local_invent_capability",
    "local_evolution_seed",
]
