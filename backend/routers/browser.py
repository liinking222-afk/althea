"""Web Browser — Althea fetches real URLs server-side and returns
title/text/links so the operator can surf the web through her.

Cross-origin iframe still works via /watch, this is for headless surfing
(reading article text, extracting links, search-style results).
Also exposes a full HTML proxy at /browser/proxy that strips X-Frame-Options
+ CSP frame-ancestors so any site can be rendered inside ALTHEA's viewport
the way Chrome would render it.
"""
import logging
import re
from datetime import datetime, timezone
from typing import List
from urllib.parse import quote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from core import db
from models import BrowserFetchRequest, Memory

router = APIRouter()

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
MAX_TEXT = 12000
MAX_PROXY_BYTES = 8 * 1024 * 1024  # 8MB per page

# Headers stripped on the way out so the browser can iframe the response
FRAME_BLOCKING_HEADERS = {
    "x-frame-options",
    "content-security-policy",
    "content-security-policy-report-only",
    "cross-origin-opener-policy",
    "cross-origin-embedder-policy",
    "cross-origin-resource-policy",
}


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url


@router.post("/browser/fetch")
async def browser_fetch(req: BrowserFetchRequest):
    url = _normalize_url(req.url)
    if not url:
        raise HTTPException(status_code=400, detail="empty_url")
    try:
        async with httpx.AsyncClient(
            timeout=12.0,
            follow_redirects=True,
            headers={"User-Agent": UA},
        ) as cx:
            r = await cx.get(url)
            final_url = str(r.url)
            content_type = r.headers.get("content-type", "")
            status = r.status_code
            html = r.text if "text/html" in content_type or "application/xhtml" in content_type else ""
            raw_text = r.text if r.text else ""
    except httpx.RequestError as e:
        # log and create a memory of the failure but still return a structured response
        await _log_fetch(url, status=0, title=None, text=f"[FETCH-FAIL] {str(e)[:160]}")
        return {
            "url": url,
            "final_url": url,
            "status": 0,
            "title": None,
            "text": "",
            "links": [],
            "error": str(e)[:200],
        }

    title = None
    text = ""
    links: List[dict] = []
    if html:
        soup = BeautifulSoup(html, "html.parser")
        title = (soup.title.string.strip() if soup.title and soup.title.string else None)
        # strip script/style
        for s in soup(["script", "style", "noscript"]):
            s.extract()
        text = re.sub(r"\n{3,}", "\n\n", soup.get_text(separator="\n").strip())[:MAX_TEXT]
        for a in soup.find_all("a", href=True)[:60]:
            href = a["href"].strip()
            if not href or href.startswith("#"):
                continue
            absolute = urljoin(final_url, href)
            label = (a.get_text() or absolute)[:120].strip()
            if not label:
                continue
            links.append({"label": label, "url": absolute})
    else:
        text = raw_text[:MAX_TEXT]

    await _log_fetch(url, status=status, title=title, text=text)

    return {
        "url": url,
        "final_url": final_url,
        "status": status,
        "title": title,
        "text": text,
        "links": links,
        "host": urlparse(final_url).hostname,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _log_fetch(url: str, status: int, title, text: str):
    try:
        mem = Memory(
            content=(
                f"[BROWSER {status} {url}] "
                + (f"title:\"{title}\" " if title else "")
                + (text[:240] if text else "")
            ),
            source="browser",
            tags=["browser", "surf"],
        )
        d = mem.model_dump()
        d["timestamp"] = d["timestamp"].isoformat()
        await db.althea_memories.insert_one(d)
    except Exception:
        logging.exception("browser memory log failed")


@router.get("/browser/history")
async def browser_history(limit: int = 30):
    docs = await db.althea_memories.find(
        {"tags": "browser"}, {"_id": 0}
    ).sort("timestamp", -1).to_list(limit)
    return {"history": docs, "count": len(docs)}
