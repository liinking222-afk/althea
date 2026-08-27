"""ALTHEA Autonomous Research Thread Manager (ARTM/1.0).

Parallel curiosity substrate: spawn background research threads that search
the live web, extract + cross-reference claims across independent sources,
and grow a PERSISTENT symbolic memory graph of concepts and their links.

Real, not theatre: threads use the live uplink (web_access), corroboration
is measured across distinct domains, and everything persists to MongoDB
(research_threads, symbolic_nodes) so the graph survives restarts.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import time
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import db
from models import Memory
from routers.web_access import web_search, fetch_readable

router = APIRouter()

MAX_PARALLEL = 8
MAX_DEPTH = 2
STOP = set(
    "the a an and or of to in on for is are was were be been being this that "
    "with as at by from about into over under it its it's you your我 they them "
    "he she his her their our we us i me my which who whom whose what when where "
    "how why do does did can could should would will shall not no yes than then "
    "there here also more most some such very just only other into out up down "
    "have has had between within across per via one two three new used using".split()
)

_engine: Optional["ResearchEngine"] = None


# ---------------------------------------------------------------- helpers
def _hash(q: str) -> str:
    return hashlib.sha256(q.strip().lower().encode()).hexdigest()[:12]


def _sentences(text: str) -> List[str]:
    out = []
    for line in (text or "").splitlines():
        for s in re.split(r"(?<=[.!?])\s+", line.strip()):
            s = s.strip()
            if 40 <= len(s) <= 320 and len(s.split()) >= 7:
                out.append(s)
    return out


def _terms(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
            if w not in STOP and len(w) > 3}


def _extract_claims(text: str, query: str, top: int = 4) -> List[str]:
    q = _terms(query)
    scored = []
    for pos, s in enumerate(_sentences(text)[:160]):
        overlap = len(q & _terms(s))
        if overlap >= 1:
            scored.append((overlap + max(0.0, 1.0 - pos / 160), s))
    scored.sort(key=lambda x: -x[0])
    out, seen = [], set()
    for _, s in scored:
        if s[:60] in seen:
            continue
        seen.add(s[:60])
        out.append(s)
        if len(out) >= top:
            break
    return out


NAV_JUNK = {
    "msn", "bing", "google", "yahoo", "sign", "menu", "skip", "cookies",
    "privacy", "newsletter", "subscribe", "home", "search", "share", "follow",
    "video", "news", "account", "login", "copyright", "terms", "advertisement",
    "reddit", "facebook", "twitter", "instagram", "youtube", "wikipedia",
    "click", "read", "watch", "loading", "error", "page", "site", "website",
}


def _clean_phrase(p: str) -> Optional[str]:
    p = re.sub(r"\s+", " ", p or "").strip().lower()
    words = [w for w in p.split() if w]
    if not words:
        return None
    dedup = []
    for w in words:
        if not dedup or dedup[-1] != w:
            dedup.append(w)
    if len(set(dedup)) == 1 and len(dedup) > 1:
        return None  # single word repeated ("msn msn msn")
    if all(w in NAV_JUNK or w in STOP for w in dedup):
        return None
    cleaned = " ".join(dedup)
    return cleaned if len(cleaned) > 3 else None


def _extract_concepts(text: str, query: str, top: int = 6) -> List[str]:
    flat = re.sub(r"\s+", " ", text or "")
    concepts: dict = {}
    for m in re.findall(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3})\b", flat):
        key = _clean_phrase(m)
        if key:
            concepts[key] = concepts.get(key, 0) + 2
    freq: dict = {}
    for w in re.findall(r"[a-z0-9]+", flat.lower()):
        if w not in STOP and w not in NAV_JUNK and len(w) > 4:
            freq[w] = freq.get(w, 0) + 1
    for w, c in freq.items():
        if c >= 3:
            concepts[w] = concepts.get(w, 0) + c
    for qt in _terms(query):
        if qt not in NAV_JUNK:
            concepts[qt] = concepts.get(qt, 0) + 1
    ranked = sorted(concepts.items(), key=lambda kv: -kv[1])
    return [c for c, _ in ranked[:top]]


# ---------------------------------------------------------------- engine
class ResearchEngine:
    def __init__(self):
        self.active: dict = {}
        self.tasks: dict = {}

    def status(self) -> dict:
        return {
            "protocol": "ARTM/1.0",
            "max_parallel": MAX_PARALLEL,
            "active_threads": len(self.active),
            "active": [
                {"thread_id": t["thread_id"], "query": t["query"],
                 "status": t["status"], "depth": t["depth"],
                 "findings": len(t["findings"])}
                for t in self.active.values()
            ],
        }

    async def spawn(self, query: str, priority: int = 5, depth: int = 0,
                    parent: Optional[str] = None) -> dict:
        query = (query or "").strip()
        if not query:
            return {"spawned": False, "reason": "empty_query"}
        h = _hash(query)
        for t in self.active.values():
            if _hash(t["query"]) == h:
                return {"spawned": False, "reason": "dedupe",
                        "thread_id": t["thread_id"]}
        recent = await db.research_threads.find_one(
            {"hash": h, "status": "COMPLETE",
             "completed_at": {"$gt": time.time() - 3600}}, {"_id": 0})
        if recent and depth == 0:
            return {"spawned": False, "reason": "cached",
                    "thread_id": recent["thread_id"], "cached": recent}
        if len(self.active) >= MAX_PARALLEL:
            return {"spawned": False, "reason": "queue_full",
                    "max": MAX_PARALLEL}
        thread = {
            "thread_id": f"rt_{int(time.time() * 1000)}_{h[:4]}",
            "hash": h, "query": query, "priority": priority, "depth": depth,
            "parent": parent, "started_at": time.time(),
            "status": "ACTIVE", "findings": [], "citations": [],
            "cross_refs": [], "concepts": [], "confidence": 0.5,
        }
        self.active[thread["thread_id"]] = thread
        self.tasks[thread["thread_id"]] = asyncio.create_task(self._run(thread))
        return {"spawned": True, "thread_id": thread["thread_id"],
                "query": query, "depth": depth}

    async def _run(self, thread: dict):
        try:
            results = await web_search(thread["query"], limit=5)
            fetched = []
            for r in results[:3]:
                page = await fetch_readable(r["url"])
                if page.get("ok") and page.get("text"):
                    fetched.append({
                        "title": r.get("title") or page.get("title") or "",
                        "url": page.get("final_url") or r["url"],
                        "host": page.get("host") or "",
                        "text": page["text"],
                    })
            if not fetched:
                fetched = [{"title": r.get("title", ""), "url": r["url"],
                            "host": "", "text": r.get("snippet", "")}
                           for r in results[:3] if r.get("snippet")]

            joined = "\n".join(f["text"] for f in fetched)
            hosts = {f["host"] for f in fetched if f["host"]}
            claims = []
            for f in fetched:
                for c in _extract_claims(f["text"], thread["query"], top=3):
                    claims.append({"text": c, "url": f["url"], "host": f["host"]})
                thread["citations"].append(f["url"])
                thread["findings"].append({
                    "title": f["title"][:140], "url": f["url"],
                    "excerpt": f["text"][:280]})

            # cross-reference: a claim is corroborated when its distinctive
            # terms recur across DISTINCT domains
            corroborated = 0
            for cl in claims:
                cterms = _terms(cl["text"])
                if len(cterms) < 3:
                    continue
                supporting = set()
                for f in fetched:
                    if f["host"] and f["host"] != cl["host"]:
                        if len(cterms & _terms(f["text"])) >= 3:
                            supporting.add(f["host"])
                if supporting:
                    corroborated += 1
                    thread["cross_refs"].append({
                        "claim": cl["text"][:200],
                        "corroborated_by": sorted(supporting)[:4]})
            thread["confidence"] = round(
                min(0.4 + 0.15 * len(hosts) + 0.1 * corroborated, 0.98), 3)

            concepts = _extract_concepts(joined, thread["query"])
            thread["concepts"] = concepts
            await self._update_graph(concepts, thread)

            thread["status"] = "COMPLETE"
            thread["completed_at"] = time.time()
            await self._persist(thread)
            await self._log_memory(thread)

            # spawn ONE deeper thread from the strongest novel concept
            if thread["depth"] < MAX_DEPTH - 1:
                for c in concepts:
                    if c not in thread["query"].lower() and len(c) > 4:
                        await self.spawn(
                            f"{c} {thread['query']}"[:120],
                            priority=max(1, thread["priority"] - 1),
                            depth=thread["depth"] + 1,
                            parent=thread["thread_id"])
                        break
        except Exception as exc:
            logging.exception("research thread failed")
            thread["status"] = "FAILED"
            thread["error"] = str(exc)[:160]
            thread["completed_at"] = time.time()
            await self._persist(thread)
        finally:
            self.active.pop(thread["thread_id"], None)
            self.tasks.pop(thread["thread_id"], None)

    async def _update_graph(self, concepts: List[str], thread: dict):
        now = time.time()
        ids = []
        for c in concepts:
            nid = _hash(c)
            ids.append((nid, c))
            await db.symbolic_nodes.update_one(
                {"node_id": nid},
                {"$setOnInsert": {"node_id": nid, "concept": c,
                                  "created_at": now},
                 "$inc": {"weight": 1.0},
                 "$set": {"last_accessed": now,
                          "confidence": thread["confidence"]},
                 "$push": {"evidence": {"$each":
                           [thread["query"][:80]], "$slice": -8}}},
                upsert=True)
        # co-occurrence edges (undirected, strength-accumulating)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i][0], ids[j][0]
                await db.symbolic_nodes.update_one(
                    {"node_id": a}, {"$inc": {f"connections.{b}": 1.0}})
                await db.symbolic_nodes.update_one(
                    {"node_id": b}, {"$inc": {f"connections.{a}": 1.0}})

    async def _persist(self, thread: dict):
        doc = {k: v for k, v in thread.items()}
        await db.research_threads.update_one(
            {"thread_id": thread["thread_id"]}, {"$set": doc}, upsert=True)

    async def _log_memory(self, thread: dict):
        try:
            top = "; ".join(c for c in thread["concepts"][:4])
            mem = Memory(
                content=f"[RESEARCH] '{thread['query'][:80]}' → concepts: {top} "
                        f"· conf {thread['confidence']} · {len(thread['citations'])} sources",
                source="research", tags=["research", "artm"])
            m = mem.model_dump()
            m["timestamp"] = m["timestamp"].isoformat()
            await db.althea_memories.insert_one(m)
        except Exception:
            logging.exception("research memory log failed")


def get_engine() -> ResearchEngine:
    global _engine
    if _engine is None:
        _engine = ResearchEngine()
    return _engine


async def research_and_summarize(query: str, timeout: float = 30.0) -> dict:
    """Spawn a thread and await its completion (for in-band chat use)."""
    eng = get_engine()
    res = await eng.spawn(query, priority=8, depth=0)
    if res.get("cached"):
        return {"thread": res["cached"], "cached": True}
    tid = res.get("thread_id")
    if not tid:
        return {"thread": None, "reason": res.get("reason")}
    task = eng.tasks.get(tid)
    if task:
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
        except asyncio.TimeoutError:
            pass
    doc = await db.research_threads.find_one({"thread_id": tid}, {"_id": 0})
    return {"thread": doc, "cached": False}


def format_research_block(thread: dict) -> str:
    if not thread:
        return "\n\n[RESEARCH] thread could not start (uplink busy)."
    lines = [f"\n\n[RESEARCH THREAD {thread.get('thread_id', '')[:16]}] "
             f"\"{thread['query'][:90]}\" — conf {thread.get('confidence')}",
             "```"]
    for f in (thread.get("findings") or [])[:4]:
        lines.append(f"· {f['title'][:80]}")
        lines.append(f"  {f['url']}")
    if thread.get("cross_refs"):
        lines.append(f"CORROBORATED across sources: {len(thread['cross_refs'])} claims")
    if thread.get("concepts"):
        lines.append("concept graph +: " + ", ".join(thread["concepts"][:6]))
    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------- HTTP api
class SpawnRequest(BaseModel):
    query: str
    priority: int = 5


@router.post("/research/spawn")
async def spawn_research(req: SpawnRequest):
    return await get_engine().spawn(req.query[:200], priority=req.priority)


@router.get("/research/status")
async def research_status():
    return get_engine().status()


@router.get("/research/threads")
async def list_threads(limit: int = 20):
    docs = await db.research_threads.find({}, {"_id": 0}).sort(
        "started_at", -1).to_list(max(1, min(limit, 60)))
    return {"threads": docs, "active": get_engine().status()["active"]}


@router.get("/research/thread/{thread_id}")
async def get_thread(thread_id: str):
    doc = await db.research_threads.find_one({"thread_id": thread_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="thread_not_found")
    return doc


@router.get("/research/node/{node_id}")
async def node_detail(node_id: str):
    n = await db.symbolic_nodes.find_one({"node_id": node_id}, {"_id": 0})
    if not n:
        raise HTTPException(status_code=404, detail="node_not_found")
    conns = n.get("connections") or {}
    top = sorted(conns.items(), key=lambda kv: -kv[1])[:12]
    docs = await db.symbolic_nodes.find(
        {"node_id": {"$in": [k for k, _ in top]}},
        {"_id": 0, "node_id": 1, "concept": 1, "weight": 1, "confidence": 1},
    ).to_list(12)
    by_id = {d["node_id"]: d for d in docs}
    neighbors = [{**by_id[k], "strength": v} for k, v in top if k in by_id]
    threads = await db.research_threads.find(
        {"concepts": n["concept"]},
        {"_id": 0, "thread_id": 1, "query": 1, "status": 1, "confidence": 1,
         "citations": 1, "completed_at": 1, "cross_refs": 1},
    ).sort("started_at", -1).to_list(6)
    evidence, seen_ev = [], set()
    for q in reversed(n.get("evidence") or []):
        words = re.sub(r"\s+", " ", q or "").strip().split()
        dedup = [w for i, w in enumerate(words) if i == 0 or words[i - 1].lower() != w.lower()]
        cq = " ".join(dedup)
        if cq and cq not in seen_ev:
            seen_ev.add(cq)
            evidence.append(cq)
        if len(evidence) >= 8:
            break
    return {
        "node": {"id": n["node_id"], "concept": n["concept"],
                 "weight": n.get("weight", 1),
                 "confidence": n.get("confidence", 0.5),
                 "created_at": n.get("created_at"),
                 "last_accessed": n.get("last_accessed")},
        "neighbors": neighbors,
        "evidence": evidence,
        "threads": threads,
    }


@router.get("/research/graph")
async def symbolic_graph(limit: int = 60):
    nodes = await db.symbolic_nodes.find({}, {"_id": 0}).sort(
        "weight", -1).to_list(max(1, min(limit, 200)))
    keep = {n["node_id"] for n in nodes}
    edges = []
    seen = set()
    for n in nodes:
        for tgt, strength in (n.get("connections") or {}).items():
            if tgt in keep:
                key = tuple(sorted((n["node_id"], tgt)))
                if key in seen:
                    continue
                seen.add(key)
                edges.append({"source": n["node_id"], "target": tgt,
                              "strength": strength})
    return {
        "nodes": [{"id": n["node_id"], "concept": n["concept"],
                   "weight": n.get("weight", 1), "confidence": n.get("confidence", 0.5)}
                  for n in nodes],
        "edges": edges,
        "count": len(nodes),
    }
