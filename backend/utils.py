"""Shared utilities: context blocks, YouTube oEmbed, TF-IDF semantic recall."""
from typing import Optional, List
import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


def build_context_block(context: Optional[dict]) -> str:
    if not context:
        return ""
    lines = ["[HOST CONTEXT]"]
    if "online" in context:
        lines.append(f"link_status={'ONLINE' if context['online'] else 'OFFLINE'}")
    if context.get("geo"):
        g = context["geo"]
        lines.append(f"gps_lock=lat:{g.get('lat'):.4f} lon:{g.get('lon'):.4f}")
    if context.get("permissions"):
        perms = ",".join([k for k, v in context["permissions"].items() if v])
        lines.append(f"granted_permissions=[{perms or 'none'}]")
    if "battery" in context:
        lines.append(f"battery={context['battery']}")
    if context.get("observation"):
        obs = context["observation"]
        url = obs.get("url") or "none"
        title = obs.get("title") or ""
        if url and url != "none":
            lines.append(
                f"currently_observing_url={url}"
                + (f" title=\"{title[:120]}\"" if title else "")
            )
        else:
            lines.append("currently_observing_url=none")
    if context.get("active_tab"):
        lines.append(f"active_center_tab={context['active_tab']}")
    if context.get("memory_count") is not None:
        lines.append(f"memory_fragments={context['memory_count']}")
    return "\n".join(lines)


async def fetch_youtube_title(url: str) -> Optional[str]:
    """Best-effort oEmbed lookup, no key required."""
    try:
        import httpx
        oembed = f"https://www.youtube.com/oembed?url={url}&format=json"
        async with httpx.AsyncClient(timeout=4.0) as cx:
            r = await cx.get(oembed)
            if r.status_code == 200:
                return r.json().get("title")
    except Exception:
        logging.exception("oembed lookup failed")
    return None


def semantic_recall(query: str, docs: List[dict], limit: int = 25) -> List[dict]:
    """
    TF-IDF cosine similarity recall.
    - Char-3-gram + word features (catches morphology + topic words)
    - Sublinear TF so a single repeated term doesn't dominate
    - English stop-word removal
    - Tag bonus: +0.15 if any query token equals one of the memory's tags
    Returns docs ranked by score desc (score in [0,1]), filtered score>0.
    """
    if not docs:
        return []
    q = (query or "").strip()
    if not q:
        return [{"score": 1.0, **d} for d in docs[:limit]]

    corpus = [
        (d.get("content", "") + " " + " ".join(d.get("tags", []) or []))
        for d in docs
    ]
    try:
        vec = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            sublinear_tf=True,
            min_df=1,
        )
        matrix = vec.fit_transform(corpus + [q])
        sims = linear_kernel(matrix[-1], matrix[:-1]).flatten()
    except ValueError:
        # corpus too small / empty
        sims = [0.0] * len(docs)

    q_tokens = {t for t in q.lower().split() if t}
    scored = []
    for d, s in zip(docs, sims):
        tag_set = {t.lower() for t in (d.get("tags", []) or [])}
        bonus = 0.15 if q_tokens & tag_set else 0.0
        score = float(min(1.0, s + bonus))
        if score > 0:
            scored.append({"score": round(score, 4), **d})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]
