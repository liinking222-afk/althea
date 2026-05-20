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


# ---------------------------------------------------------------------------
# FULL HTML PROXY  /api/browser/proxy?url=...
# Strips X-Frame-Options / CSP, rewrites links + asset srcs to flow through
# the proxy so the operator can iframe ANY site that does not actively detect
# proxies. Login-walled SPAs (Twitter, Gmail) and Cloudflare-gated sites may
# still refuse, but ~80% of the open web renders fine.
# ---------------------------------------------------------------------------
URL_ATTRS = ("href", "src", "action", "data-src", "srcset", "poster")


def _proxy_url(absolute: str, base_api: str) -> str:
    return f"{base_api}/browser/asset?url={quote(absolute, safe='')}"


def _rewrite_srcset(value: str, page_url: str, base_api: str) -> str:
    parts = []
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        bits = chunk.split()
        if not bits:
            continue
        absolute = urljoin(page_url, bits[0])
        parts.append(" ".join([_proxy_url(absolute, base_api)] + bits[1:]))
    return ", ".join(parts)


def _rewrite_html(html: str, page_url: str, base_api: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Inject <base> so relative URLs resolve, even though we rewrite most of
    # them. Some inline JS uses document.baseURI.
    head = soup.find("head")
    if head:
        base = soup.new_tag("base", href=page_url)
        head.insert(0, base)
        # Drop CSP <meta> tags so the iframe is not double-locked.
        for m in head.find_all(
            "meta",
            attrs={
                "http-equiv": re.compile(
                    r"content-security-policy|x-frame-options", re.I,
                )
            },
        ):
            m.extract()

    # Walk every element with a URL attribute and rewrite through the proxy.
    for tag in soup.find_all(True):
        if tag.name == "base":
            continue
        for attr in URL_ATTRS:
            if attr not in tag.attrs:
                continue
            value = tag.attrs[attr]
            if not isinstance(value, str):
                continue
            if value.startswith(("data:", "javascript:", "mailto:", "tel:", "#")):
                continue
            if attr == "srcset":
                tag.attrs[attr] = _rewrite_srcset(value, page_url, base_api)
                continue
            absolute = urljoin(page_url, value.strip())
            if tag.name == "a" and attr == "href":
                # Anchor clicks should re-enter the HTML proxy (not asset).
                tag.attrs[attr] = (
                    f"{base_api}/browser/proxy?url={quote(absolute, safe='')}"
                )
                tag.attrs["target"] = "_self"
                continue
            if tag.name == "form" and attr == "action":
                tag.attrs[attr] = (
                    f"{base_api}/browser/proxy?url={quote(absolute, safe='')}"
                )
                continue
            tag.attrs[attr] = _proxy_url(absolute, base_api)

    # Tiny status badge so the operator knows they are inside Althea's proxy.
    badge = soup.new_tag("div")
    badge["style"] = (
        "position:fixed;bottom:8px;right:8px;z-index:2147483647;"
        "font:10px/1.2 monospace;letter-spacing:1px;text-transform:uppercase;"
        "color:#CCFF00;background:rgba(0,0,0,0.6);"
        "padding:4px 8px;border:1px solid rgba(204,255,0,0.35);"
        "pointer-events:none;backdrop-filter:blur(4px);"
    )
    badge.string = "althea // surf-proxy"
    body = soup.find("body")
    if body:
        body.append(badge)

    return str(soup)


def _strip_frame_headers(headers: dict) -> dict:
    cleaned = {}
    for k, v in headers.items():
        if k.lower() in FRAME_BLOCKING_HEADERS:
            continue
        if k.lower() in ("content-encoding", "content-length", "transfer-encoding"):
            # httpx already decoded the body; pass-through length is wrong.
            continue
        cleaned[k] = v
    return cleaned


def _base_api(request: Request) -> str:
    # Build "<scheme>://<host>/api" regardless of ingress.
    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{scheme}://{host}/api"


@router.get("/browser/proxy")
async def browser_proxy(request: Request, url: str):
    target = _normalize_url(url)
    if not target:
        raise HTTPException(status_code=400, detail="empty_url")

    # Smart YouTube redirect → embed (no proxy needed, YouTube allows /embed/).
    try:
        parsed = urlparse(target)
        host = (parsed.hostname or "").replace("www.", "")
        if host in ("youtube.com", "m.youtube.com"):
            from urllib.parse import parse_qs
            v = parse_qs(parsed.query).get("v", [None])[0]
            if v:
                target = f"https://www.youtube.com/embed/{v}?autoplay=1"
        elif host == "youtu.be":
            vid = parsed.path.lstrip("/")
            if vid:
                target = f"https://www.youtube.com/embed/{vid}?autoplay=1"
    except Exception:
        logging.exception("youtube rewrite failed")

    base_api = _base_api(request)

    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as cx:
            r = await cx.get(target)
            content = r.content[:MAX_PROXY_BYTES]
            content_type = r.headers.get("content-type", "text/html").lower()
            final_url = str(r.url)
    except httpx.RequestError as e:
        return HTMLResponse(
            f"<html><body style='font:14px monospace;color:#FF2A2A;"
            f"background:#000;padding:24px;'>[PROXY-FAIL] {str(e)[:240]}</body></html>",
            status_code=502,
        )

    headers = _strip_frame_headers(dict(r.headers))

    if "text/html" in content_type:
        try:
            html = content.decode(r.encoding or "utf-8", errors="ignore")
        except Exception:
            html = content.decode("utf-8", errors="ignore")
        rewritten = _rewrite_html(html, final_url, base_api)
        headers["content-type"] = "text/html; charset=utf-8"
        return HTMLResponse(content=rewritten, status_code=r.status_code, headers=headers)

    # Non-HTML (PDF, image served directly etc.) → pass straight through.
    return Response(content=content, status_code=r.status_code, headers=headers, media_type=content_type)


@router.get("/browser/asset")
async def browser_asset(request: Request, url: str):
    """Stream any sub-resource (CSS/JS/image/font) referenced by the proxied page."""
    target = _normalize_url(url)
    if not target:
        raise HTTPException(status_code=400, detail="empty_url")

    base_api = _base_api(request)
    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={
                "User-Agent": UA,
                "Accept": "*/*",
                "Referer": target,
            },
        ) as cx:
            r = await cx.get(target)
            content = r.content[:MAX_PROXY_BYTES]
            content_type = r.headers.get("content-type", "application/octet-stream").lower()
    except httpx.RequestError as e:
        return Response(
            content=f"/* proxy fail: {str(e)[:140]} */",
            status_code=502,
            media_type="text/plain",
        )

    headers = _strip_frame_headers(dict(r.headers))

    # Rewrite CSS url(...) and @import so background-images and fonts still
    # load through the proxy.
    if "text/css" in content_type:
        try:
            css = content.decode("utf-8", errors="ignore")
        except Exception:
            css = ""
        def _sub(m):
            raw = m.group(1).strip("'\"")
            if raw.startswith(("data:", "#")):
                return m.group(0)
            absolute = urljoin(target, raw)
            return f"url({_proxy_url(absolute, base_api)})"
        css = re.sub(r"url\(([^)]+)\)", _sub, css)
        return Response(content=css, status_code=r.status_code, headers=headers, media_type="text/css; charset=utf-8")

    return Response(content=content, status_code=r.status_code, headers=headers, media_type=content_type)
