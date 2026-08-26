"""ALTHEA Live-Drive Browser — a REAL headless Chromium she pilots.

Unlike the HTML proxy (routers/browser.py), this drives an actual browser:
JavaScript runs, sessions persist, and the operator sees live JPEG frames
and steers with clicks / typing / scrolling. Frames are delivered by
lightweight polling so it works through any ingress on any device.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
import re
import time
import uuid
from typing import Optional
from urllib.parse import quote, urlparse, parse_qs

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
_last_sid: Optional[str] = None


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
    global _last_sid
    _last_sid = sid
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


# ---------------- AUTO-PILOT — Althea drives the browser herself ----------
LEAD_IN_RE = re.compile(
    r"^(?:hey\s+)?(?:althea[,\s]*)?(?:please\s+)?(?:go\s+)?(?:find|search|look\s*up|browse|hunt|shop)"
    r"(?:\s+(?:me|for|the\s+web\s+for|online\s+for|up))*\s*",
    re.IGNORECASE,
)


def _extract_query(goal: str) -> str:
    q = re.sub(r"\b(autopilot|auto-pilot|drive the browser( to)?|and click.*$|"
               r"then click.*$|watch you.*$)\b", " ", goal or "", flags=re.IGNORECASE)
    q = LEAD_IN_RE.sub("", q.strip())
    q = re.sub(r"\s{2,}", " ", q).strip(" .!?")
    return q or (goal or "").strip()


def _score_sentences(text: str, query: str, max_n: int = 4):
    stop = set("the a an and or of to in on for is are was were be i you it "
               "this that with as at by from about me my find go".split())
    q_terms = {w for w in re.findall(r"[a-z0-9]+", query.lower())
               if w not in stop and len(w) > 2}
    scored = []
    for line in (text or "").splitlines():
        for pos, s in enumerate(re.split(r"(?<=[.!?])\s+", line.strip())):
            s = s.strip()
            if not (40 <= len(s) <= 380 and len(s.split()) >= 7):
                continue
            overlap = len(q_terms & set(re.findall(r"[a-z0-9]+", s.lower())))
            if overlap >= 1:
                scored.append((overlap, s))
    scored.sort(key=lambda x: -x[0])
    out, seen = [], set()
    for _, s in scored:
        if s[:60] in seen:
            continue
        seen.add(s[:60])
        out.append(s)
        if len(out) >= max_n:
            break
    return out


async def run_autopilot(goal: str) -> dict:
    """Procedural autopilot (ZERO LLM): open the search engine, visibly type
    the query, press Enter, click the first organic result, scroll, read,
    and return findings. Drives the operator's open DRIVE session if one
    exists so they can literally watch her work."""
    query = _extract_query(goal)
    log = []
    async with _lock:
        await _ensure_browser()
    sid = _last_sid if _last_sid in _sessions else None
    if not sid:
        res = await create_session(SessionRequest(url="https://www.bing.com"))
        sid = res["sid"]
    s = _get(sid)
    page = s["page"]
    context = s["context"]
    landed_title, findings = "", []
    try:
        log.append("navigate → bing.com")
        await page.goto("https://www.bing.com", timeout=25000,
                        wait_until="domcontentloaded")
        await page.wait_for_timeout(900)
        box = await page.query_selector(
            "#sb_form_q, input[name=q], textarea[name=q]")
        if box:
            await box.click()
            await page.keyboard.type(query[:120], delay=40)  # visible typing
            log.append(f'type "{query[:60]}" → ENTER')
            await page.keyboard.press("Enter")
        else:
            log.append(f'search "{query[:60]}" (direct)')
            await page.goto(f"https://www.bing.com/search?q={quote(query)}",
                            timeout=25000, wait_until="domcontentloaded")
        try:
            await page.wait_for_selector("#b_results li.b_algo h2 a", timeout=12000)
        except Exception:
            pass
        await page.wait_for_timeout(1200)
        links = await page.query_selector_all("#b_results li.b_algo h2 a")
        target_href, target_title = None, None
        for link in links[:6]:
            href = (await link.get_attribute("href")) or ""
            # Bing wraps organics in /ck/ redirects — decode to the real URL
            if "bing.com/ck/" in href:
                qs = parse_qs(urlparse(href).query)
                u = (qs.get("u") or [""])[0]
                href = ""
                if u.startswith("a1"):
                    pad = u[2:] + "=" * (-len(u[2:]) % 4)
                    try:
                        href = base64.urlsafe_b64decode(pad).decode("utf-8", "ignore")
                    except Exception:
                        href = ""
            if not href.startswith("http"):
                continue
            host = urlparse(href).netloc
            if "bing.com" in host or any(
                    bad in href for bad in ("adclick", "doubleclick", "aclk")):
                continue
            target_href = href
            target_title = ((await link.inner_text()) or "")[:90]
            try:
                await link.hover()
            except Exception:
                pass
            break
        if target_href:
            log.append(f'click first organic result → "{target_title}"')
            try:
                await page.goto(target_href, timeout=25000,
                                wait_until="domcontentloaded")
            except Exception:
                pass
            await page.wait_for_timeout(1500)
        else:
            log.append("no organic result link found — staying on results page")
        for _ in range(2):
            await page.mouse.wheel(0, 700)
            await page.wait_for_timeout(650)
        log.append("scroll · reading page")
        try:
            landed_title = (await page.title())[:110]
        except Exception:
            pass
        try:
            body_text = await page.evaluate(
                "document.body ? document.body.innerText.slice(0, 20000) : ''")
            findings = _score_sentences(body_text, query)
        except Exception:
            pass
    except Exception as e:
        log.append(f"fault: {str(e)[:90]}")
    return {"sid": sid, "goal": goal, "query": query, "log": log,
            "landed_url": page.url, "landed_title": landed_title,
            "findings": findings}


class AutopilotRequest(BaseModel):
    goal: str


@router.post("/live/autopilot")
async def autopilot_endpoint(req: AutopilotRequest):
    if not (req.goal or "").strip():
        raise HTTPException(status_code=400, detail="empty_goal")
    try:
        return await run_autopilot(req.goal[:300])
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("autopilot failed")
        raise HTTPException(status_code=503,
                            detail=f"autopilot unavailable: {str(e)[:120]}")


def format_autopilot_block(ap: dict) -> str:
    lines = [f"\n\n[AUTOPILOT /live-drive] goal: \"{ap['goal'][:110]}\" (0 credits)",
             "```"]
    for step in ap["log"]:
        lines.append(f"> {step}")
    lines.append(f"LANDED: {ap['landed_title'] or '(untitled)'}")
    lines.append(f"        {ap['landed_url']}")
    if ap["findings"]:
        lines.append("FINDINGS:")
        for f in ap["findings"]:
            lines.append(f"  · {f}")
    lines.append("```")
    lines.append("_watch me drive: BROWSER tab → DRIVE mode_")
    return "\n".join(lines)
