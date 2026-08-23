"""ALTHEA — Live Internet Uplink.

Gives Althea autonomous, keyless access to the whole open web so she can
"go anywhere on the internet" and ground her replies in live data.

Zero extra LLM credits: search + page-fetch are pure server-side httpx +
BeautifulSoup. The fetched context is folded into the SAME single chat LLM
call that already happens, so grounding costs nothing extra.

  · web_search(query)          — keyless DuckDuckGo results (title/url/snippet)
  · fetch_readable(url)        — clean article text + link graph
  · inband_web_uplink(msg)     — auto-detect a lookup intent, fetch live data,
                                 return a context block for the system prompt
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import quote, urljoin, urlparse, parse_qs, unquote

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import db
from models import Memory

router = APIRouter()

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MAX_TEXT = 6000
URL_RE = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)

# Phrases that mean "please reach out to the live internet".
UPLINK_TRIGGERS = re.compile(
    r"\b(search|look\s?up|lookup|google|browse|go to|navigate|latest|current|"
    r"today'?s?|right now|news|headlines?|weather in|price of|stock|score|"
    r"who is|what is happening|whats happening|what'?s new|find online|"
    r"on the internet|online|website|web page|url)\b",
    re.IGNORECASE,
)


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url


async def _log(content: str, tags: List[str]):
    try:
        mem = Memory(content=content[:480], source="uplink", tags=tags)
        d = mem.model_dump()
        d["timestamp"] = d["timestamp"].isoformat()
        await db.althea_memories.insert_one(d)
    except Exception:
        logging.exception("uplink memory log failed")


# ---------- keyless web search (DuckDuckGo HTML, no API key) ----------
async def web_search(query: str, limit: int = 6) -> List[dict]:
    q = (query or "").strip()
    if not q:
        return []
    endpoints = [
        f"https://html.duckduckgo.com/html/?q={quote(q)}",
        f"https://lite.duckduckgo.com/lite/?q={quote(q)}",
    ]
    results: List[dict] = []
    async with httpx.AsyncClient(
        timeout=12.0, follow_redirects=True,
        headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
    ) as cx:
        for url in endpoints:
            try:
                r = await cx.get(url)
            except httpx.RequestError:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            # html.duckduckgo.com layout
            for res in soup.select("div.result, div.web-result"):
                a = res.select_one("a.result__a")
                if not a:
                    continue
                href = a.get("href", "")
                # DDG wraps target in a redirect ?uddg=
                if "duckduckgo.com/l/" in href or "uddg=" in href:
                    qs = parse_qs(urlparse(href).query)
                    href = unquote(qs.get("uddg", [href])[0])
                snip = res.select_one(".result__snippet")
                results.append({
                    "title": a.get_text(strip=True),
                    "url": href,
                    "snippet": (snip.get_text(" ", strip=True) if snip else "")[:300],
                })
                if len(results) >= limit:
                    break
            # lite layout fallback
            if not results:
                for a in soup.select("a.result-link"):
                    href = a.get("href", "")
                    if "uddg=" in href:
                        qs = parse_qs(urlparse(href).query)
                        href = unquote(qs.get("uddg", [href])[0])
                    results.append({
                        "title": a.get_text(strip=True),
                        "url": href, "snippet": "",
                    })
                    if len(results) >= limit:
                        break
            if results:
                break
    return results[:limit]


# ---------- fetch + extract readable text ----------
async def fetch_readable(url: str) -> dict:
    target = _normalize_url(url)
    if not target:
        return {"ok": False, "error": "empty_url"}
    try:
        async with httpx.AsyncClient(
            timeout=14.0, follow_redirects=True,
            headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"},
        ) as cx:
            r = await cx.get(target)
            html = r.text
            final_url = str(r.url)
            status = r.status_code
    except httpx.RequestError as e:
        return {"ok": False, "error": str(e)[:200], "url": target}

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    for s in soup(["script", "style", "noscript", "svg", "form"]):
        s.extract()
    text = re.sub(r"\n{3,}", "\n\n", soup.get_text(separator="\n").strip())[:MAX_TEXT]
    links = []
    for a in soup.find_all("a", href=True)[:40]:
        href = a["href"].strip()
        if not href or href.startswith("#"):
            continue
        label = (a.get_text() or "")[:100].strip()
        if label:
            links.append({"label": label, "url": urljoin(final_url, href)})
    return {
        "ok": True, "url": target, "final_url": final_url, "status": status,
        "title": title, "text": text, "links": links,
        "host": urlparse(final_url).hostname,
    }


# ---------- the in-band uplink hook (called by chat.py) ----------
async def inband_web_uplink(user_message: str) -> Optional[str]:
    """If the operator's message implies a live lookup, reach the internet
    and return a context block to inject into the system prompt. Returns None
    when nothing fired. Never raises — degrades to None on any failure."""
    text = (user_message or "").strip()
    if not text:
        return None

    try:
        # 1) explicit URL in the message → fetch that page directly
        url_match = URL_RE.search(text)
        if url_match:
            page = await fetch_readable(url_match.group(0))
            if page.get("ok"):
                await _log(
                    f"[UPLINK fetch {page.get('status')}] {page.get('final_url')} :: "
                    f"{(page.get('title') or '')[:120]}",
                    ["uplink", "fetch"],
                )
                block = [
                    f"[LIVE INTERNET UPLINK — fetched {datetime.now(timezone.utc).isoformat()}]",
                    f"URL: {page.get('final_url')}",
                    f"TITLE: {page.get('title') or '(none)'}",
                    "PAGE TEXT (live, truncated):",
                    page.get("text", "")[:4000],
                    "",
                    "Ground your reply in this live page. Cite the URL. If it is "
                    "irrelevant or blank, say the page could not be read.",
                ]
                return "\n".join(block)
            return None

        # 2) lookup intent → keyless web search + fetch top result
        if not UPLINK_TRIGGERS.search(text):
            return None
        # trim command noise / lead-ins to form a clean query
        query = re.sub(
            r"^(please\s+|can you\s+|could you\s+|hey\s+althea[,\s]*|althea[,\s]*)",
            "", text, flags=re.IGNORECASE,
        ).strip()
        results = await web_search(query, limit=6)
        if not results:
            return None
        await _log(
            f"[UPLINK search] '{query[:120]}' → {len(results)} results",
            ["uplink", "search"],
        )
        lines = [
            f"[LIVE INTERNET UPLINK — searched {datetime.now(timezone.utc).isoformat()}]",
            f"QUERY: {query}",
            "TOP RESULTS:",
        ]
        for i, res in enumerate(results, 1):
            lines.append(f"{i}. {res['title']} — {res['url']}")
            if res.get("snippet"):
                lines.append(f"   {res['snippet']}")

        # Fetch the top result's text so Althea can answer, not just link.
        top = next((r for r in results if r.get("url", "").startswith("http")), None)
        if top:
            page = await fetch_readable(top["url"])
            if page.get("ok") and page.get("text"):
                lines.append("")
                lines.append(f"EXCERPT FROM TOP RESULT ({page.get('host')}):")
                lines.append(page["text"][:3000])
        lines.append("")
        lines.append(
            "Ground your reply in these live results. Synthesize an answer and "
            "cite the source URL(s). This is real, current internet data."
        )
        return "\n".join(lines)
    except Exception:
        logging.exception("inband_web_uplink failed")
        return None


# ---------- HTTP api ----------
class SearchRequest(BaseModel):
    query: str
    limit: int = 6


class FetchRequest(BaseModel):
    url: str


@router.post("/web/search")
async def http_search(req: SearchRequest):
    results = await web_search(req.query, limit=max(1, min(req.limit, 15)))
    await _log(f"[UPLINK search] '{req.query[:120]}' → {len(results)} results",
               ["uplink", "search"])
    return {"query": req.query, "count": len(results), "results": results}


@router.post("/web/fetch")
async def http_fetch(req: FetchRequest):
    page = await fetch_readable(req.url)
    if not page.get("ok"):
        raise HTTPException(status_code=502, detail=page.get("error", "fetch_failed"))
    await _log(f"[UPLINK fetch {page.get('status')}] {page.get('final_url')}",
               ["uplink", "fetch"])
    return page


@router.get("/web/status")
async def uplink_status():
    """Quick connectivity probe so the operator can confirm the uplink is live."""
    online = False
    detail = ""
    try:
        async with httpx.AsyncClient(timeout=6.0, headers={"User-Agent": UA}) as cx:
            r = await cx.get("https://duckduckgo.com/")
            online = r.status_code < 500
            detail = f"HTTP {r.status_code}"
    except Exception as e:
        detail = str(e)[:160]
    return {
        "uplink": "online" if online else "offline",
        "detail": detail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


__all__ = ["router", "web_search", "fetch_readable", "inband_web_uplink"]
