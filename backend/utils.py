"""Shared utilities: context blocks, YouTube oEmbed, TF-IDF semantic recall."""
from typing import Optional, List
import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


def build_context_block(context: Optional[dict]) -> str:
    if not context:
        return ""
    lines = ["[HOST CONTEXT]"]
    if context.get("shared_room"):
        r = context["shared_room"]
        lines = ["[SHARED ROOM — you are the ONE Althea shared by this private conversation]",
                 f"participants={', '.join(r.get('participants') or [])}",
                 f"speaking_to_you_now={r.get('speaker')}",
                 "You can see their human-to-human conversation below (most recent last). "
                 "Both participants see everything you say here. Address people by name."]
        if r.get("autonomous"):
            lines.append("MODE=autonomous jump-in: you were not addressed. Be brief and only "
                         "speak if genuinely useful; otherwise answer exactly [silent].")
        if r.get("transcript"):
            lines.append("[HUMAN CONVERSATION — verbatim]")
            lines.extend(r["transcript"])
        lines.append("")
        lines.append("[HOST CONTEXT]")
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
    if context.get("device"):
        d = context["device"]
        parts = []
        if d.get("platform"):
            parts.append(f"platform={d['platform']}")
        if d.get("ua_mobile") is not None:
            parts.append("form=mobile" if d["ua_mobile"] else "form=desktop")
        if d.get("battery"):
            parts.append(f"battery={d['battery']}")
        if d.get("network"):
            parts.append(f"net={d['network']}")
        if d.get("geo"):
            g = d["geo"]
            if g.get("lat") is not None:
                parts.append(f"loc={g['lat']:.4f},{g['lon']:.4f}")
        if d.get("orientation"):
            o = d["orientation"]
            parts.append(f"tilt={o.get('tilt_fb')}/{o.get('tilt_lr')}")
        if d.get("camera"):
            parts.append(f"camera={d['camera']}")
        if parts:
            lines.append("device[" + " ".join(parts) + "]")
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


async def next_node_id(db) -> str:
    """Sequential NODE-XXXX id. Shared by routers/observe.py and routers/lattice.py."""
    count = await db.althea_nodes.count_documents({})
    return f"NODE-{count:04d}"


def semantic_recall(query: str, docs: List[dict], limit: int = 25) -> List[dict]:
    """
    Hybrid TF-IDF cosine recall:
    - char_wb (3-5) catches morphology / partial matches
    - word (1-2) catches topic-level lexical overlap
    Take max of the two per-doc similarities, then add a tag bonus.
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

    def _sims(analyzer: str, ngram_range):
        try:
            vec = TfidfVectorizer(
                analyzer=analyzer,
                ngram_range=ngram_range,
                sublinear_tf=True,
                min_df=1,
                stop_words="english" if analyzer == "word" else None,
            )
            matrix = vec.fit_transform(corpus + [q])
            return linear_kernel(matrix[-1], matrix[:-1]).flatten()
        except ValueError:
            return [0.0] * len(docs)

    char_sims = _sims("char_wb", (3, 5))
    word_sims = _sims("word", (1, 2))

    import re
    q_tokens = {t for t in re.findall(r"[a-z0-9]+", q.lower()) if t}
    scored = []
    for d, cs, ws in zip(docs, char_sims, word_sims):
        tag_set = {t.lower() for t in (d.get("tags", []) or [])}
        tag_bonus = 0.15 if q_tokens & tag_set else 0.0

        # Explicit query-token coverage: fraction of query tokens that appear
        # literally in this doc. Strong signal for short queries against a
        # tiny corpus where TF-IDF magnitudes stay low.
        if q_tokens:
            doc_tokens = set(
                re.findall(
                    r"[a-z0-9]+",
                    (d.get("content", "") + " " + " ".join(d.get("tags", []) or [])).lower(),
                )
            )
            coverage = len(q_tokens & doc_tokens) / len(q_tokens)
        else:
            coverage = 0.0
        coverage_bonus = 0.5 * coverage

        base = max(float(cs), float(ws))
        score = float(min(1.0, base + coverage_bonus + tag_bonus))
        if score > 0:
            scored.append({"score": round(score, 4), **d})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]
