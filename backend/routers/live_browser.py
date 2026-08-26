"""ALTHEA Live-Drive Browser — a REAL headless Chromium she pilots.

Unlike the HTML proxy (routers/browser.py), this drives an actual browser:
JavaScript runs, sessions persist, and the operator sees live JPEG frames
and steers with clicks / typing / scrolling. Frames are delivered by
lightweight polling so it works through any ingress on any device.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter()

VIEW_W, VIEW_H = 1280, 800
IDLE_SECONDS = 300
MAX_SESSIONS = 4
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_pw = None
_browser = None
_sessions: dict = {}
_lock = asyncio.Lock()


CHROMIUM_CANDIDATES = [
    os.environ.get("PLAYWRIGHT_CHROME_EXECUTABLE_PATH") or "",
    "/usr/local/bin/browser-use-chromium",
    "/pw-browsers/chromium_headless_shell-1208/chrome-linux/headless_shell",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


async def _ensure_browser():
    global _pw, _browser
    if _browser:
        return
    from playwright.async_api import async_playwright
    _pw = await async_playwright().start()
    exe = next((c for c in CHROMIUM_CANDIDATES if c and os.path.exists(c)), None)
    try:
        if exe:
            _browser = await _pw.chromium.launch(headless=True, executable_path=exe)
        else:
            _browser = await _pw.chromium.launch(headless=True)
    except Exception:
        _browser = await _pw.chromium.launch(headless=True)


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return "https://www.wikipedia.org"
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


async def _reap_idle():
    now = time.time()
    for sid in list(_sessions):
        if now - _sessions[sid]["last"] > IDLE_SECONDS:
            await _close_session(sid)


async def _close_session(sid: str):
    s = _sessions.pop(sid, None)
    if not s:
        return
    try:
        await s["context"].close()
    except Exception:
        pass


def _get(sid: str) -> dict:
    s = _sessions.get(sid)
    if not s:
        raise HTTPException(status_code=404, detail="session_not_found")
    s["last"] = time.time()
    return s


class SessionRequest(BaseModel):
    url: Optional[str] = None


class CmdRequest(BaseModel):
    sid: str
    action: str
    url: Optional[str] = None
    x: Optional[float] = None  # normalized 0..1
    y: Optional[float] = None
    text: Optional[str] = None
    key: Optional[str] = None
    delta: Optional[float] = None


@router.post("/live/session")
async def create_session(req: SessionRequest):
    async with _lock:
        try:
            await _ensure_browser()
        except Exception as e:
            logging.exception("live browser launch failed")
            raise HTTPException(
                status_code=503,
                detail=f"live-browser engine unavailable: {str(e)[:120]}",
            )
        await _reap_idle()
        if len(_sessions) >= MAX_SESSIONS:
            oldest = min(_sessions, key=lambda k: _sessions[k]["last"])
            await _close_session(oldest)
    context = await _browser.new_context(
        viewport={"width": VIEW_W, "height": VIEW_H}, user_agent=UA,
    )
    page = await context.new_page()
    sid = uuid.uuid4().hex[:12]
    _sessions[sid] = {"context": context, "page": page, "last": time.time()}
    try:
        await page.goto(_normalize_url(req.url), timeout=25000,
                        wait_until="domcontentloaded")
    except Exception:
        pass
    return {"sid": sid, "url": page.url,
            "viewport": {"w": VIEW_W, "h": VIEW_H}}


@router.post("/live/cmd")
async def live_cmd(req: CmdRequest):
    s = _get(req.sid)
    page = s["page"]
    try:
        if req.action == "navigate":
            await page.goto(_normalize_url(req.url), timeout=25000,
                            wait_until="domcontentloaded")
        elif req.action == "click":
            await page.mouse.click(
                max(0.0, min(1.0, req.x or 0)) * VIEW_W,
                max(0.0, min(1.0, req.y or 0)) * VIEW_H,
            )
        elif req.action == "type":
            await page.keyboard.type((req.text or "")[:500], delay=15)
        elif req.action == "key":
            await page.keyboard.press((req.key or "Enter")[:24])
        elif req.action == "scroll":
            await page.mouse.wheel(0, float(req.delta or 400))
        elif req.action == "back":
            await page.go_back(timeout=15000)
        elif req.action == "forward":
            await page.go_forward(timeout=15000)
        elif req.action == "reload":
            await page.reload(timeout=25000)
        else:
            raise HTTPException(status_code=400, detail="unknown_action")
    except HTTPException:
        raise
    except Exception as e:
        return {"ok": False, "error": str(e)[:160], "url": page.url}
    title = ""
    try:
        title = await page.title()
    except Exception:
        pass
    return {"ok": True, "url": page.url, "title": title}


@router.get("/live/frame/{sid}")
async def live_frame(sid: str):
    s = _get(sid)
    try:
        shot = await s["page"].screenshot(type="jpeg", quality=55)
    except Exception:
        raise HTTPException(status_code=409, detail="frame_unavailable")
    return Response(content=shot, media_type="image/jpeg",
                    headers={"Cache-Control": "no-store"})


@router.get("/live/state/{sid}")
async def live_state(sid: str):
    s = _get(sid)
    title = ""
    try:
        title = await s["page"].title()
    except Exception:
        pass
    return {"url": s["page"].url, "title": title,
            "sessions": len(_sessions)}


@router.delete("/live/session/{sid}")
async def delete_session(sid: str):
    await _close_session(sid)
    return {"closed": sid}
