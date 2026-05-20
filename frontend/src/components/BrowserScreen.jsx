import React, { useState, useCallback, useRef, useEffect, useMemo } from "react";
import axios from "axios";
import { API } from "@/App";
import {
    Globe,
    ArrowLeft,
    ArrowRight,
    RotateCw,
    Loader2,
    ExternalLink,
    Search,
    BookOpen,
    Monitor,
    Home,
    Shield,
} from "lucide-react";

const HOME_TARGETS = [
    { label: "wikipedia // consciousness", url: "https://en.wikipedia.org/wiki/Consciousness" },
    { label: "openstreetmap", url: "https://www.openstreetmap.org" },
    { label: "youtube // first ever", url: "https://www.youtube.com/watch?v=jNQXAC9IVRw" },
    { label: "archive.org", url: "https://archive.org" },
    { label: "hacker news", url: "https://news.ycombinator.com" },
    { label: "stellarium sky map", url: "https://stellarium-web.org/" },
    { label: "example.com", url: "https://example.com" },
    { label: "mdn web docs", url: "https://developer.mozilla.org" },
];

function normalizeInput(raw) {
    const value = (raw || "").trim();
    if (!value) return "";
    if (/^https?:\/\//i.test(value)) return value;
    // If it has a dot and no spaces, treat as domain. Otherwise → DuckDuckGo search.
    if (/^[^\s]+\.[^\s]+$/.test(value)) return "https://" + value;
    return "https://duckduckgo.com/?q=" + encodeURIComponent(value);
}

// Sites that already permit iframe embedding via a dedicated /embed/ path —
// we bypass the proxy for these because (a) they work natively and (b) the
// proxy would double-wrap their CSP-nonced player scripts and break playback.
function directEmbedFor(rawUrl) {
    try {
        const u = new URL(rawUrl);
        const host = u.hostname.replace(/^www\./, "").replace(/^m\./, "");
        if (host === "youtube.com" || host === "youtube-nocookie.com") {
            const v = u.searchParams.get("v");
            if (v) return `https://www.youtube.com/embed/${v}`;
            if (u.pathname.startsWith("/embed/")) return rawUrl;
            if (u.pathname.startsWith("/shorts/")) {
                const id = u.pathname.split("/")[2];
                if (id) return `https://www.youtube.com/embed/${id}`;
            }
        }
        if (host === "youtu.be") {
            const id = u.pathname.replace("/", "").split("?")[0];
            if (id) return `https://www.youtube.com/embed/${id}`;
        }
        if (host === "vimeo.com") {
            const id = u.pathname.split("/").filter(Boolean)[0];
            if (id && /^\d+$/.test(id)) return `https://player.vimeo.com/video/${id}`;
        }
        if (host === "twitch.tv") {
            const seg = u.pathname.split("/").filter(Boolean);
            if (seg.length === 1) {
                return `https://player.twitch.tv/?channel=${seg[0]}&parent=${window.location.hostname}`;
            }
        }
    } catch (_e) {
        // ignore — fall through to proxy
    }
    return null;
}

const BrowserScreen = ({ onWatch }) => {
    const [url, setUrl] = useState("");
    const [draft, setDraft] = useState("");
    const [mode, setMode] = useState("live"); // "live" (iframe via proxy) | "reader" (text+links)
    const [history, setHistory] = useState([]);
    const [historyIdx, setHistoryIdx] = useState(-1);
    const [readerPage, setReaderPage] = useState(null);
    const [loading, setLoading] = useState(false);
    const [iframeKey, setIframeKey] = useState(0);
    const inputRef = useRef(null);

    const proxySrc = useMemo(() => {
        if (!url) return "";
        // Prefer a direct embed for sites with a dedicated /embed/ that
        // already allows iframes (YouTube, Vimeo, Twitch). The proxy can't
        // re-host their CSP-nonced player scripts cleanly.
        const direct = directEmbedFor(url);
        if (direct) return direct;
        return `${API}/browser/proxy?url=${encodeURIComponent(url)}`;
    }, [url]);

    const isDirectEmbed = useMemo(() => !!(url && directEmbedFor(url)), [url]);

    const pushHistory = useCallback(
        (u) => {
            setHistory((h) => {
                const next = h.slice(0, historyIdx + 1);
                if (next[next.length - 1] !== u) next.push(u);
                return next.slice(-50);
            });
            setHistoryIdx((i) => i + 1);
        },
        [historyIdx],
    );

    const fetchReader = useCallback(async (u) => {
        setLoading(true);
        try {
            const res = await axios.post(`${API}/browser/fetch`, { url: u });
            setReaderPage(res.data);
        } catch (e) {
            setReaderPage({
                url: u,
                status: 0,
                error: e.message,
                text: "",
                links: [],
            });
        } finally {
            setLoading(false);
        }
    }, []);

    const navigate = useCallback(
        (target, opts = {}) => {
            const u = normalizeInput(target ?? draft);
            if (!u) return;
            setUrl(u);
            setDraft(u);
            setIframeKey((k) => k + 1);
            if (!opts.skipHistory) pushHistory(u);
            if (mode === "reader") fetchReader(u);
            else setLoading(true);
        },
        [draft, pushHistory, mode, fetchReader],
    );

    // When iframe finishes loading, drop the spinner.
    const onIframeLoad = () => setLoading(false);

    const goBack = () => {
        if (historyIdx <= 0) return;
        const next = historyIdx - 1;
        setHistoryIdx(next);
        const u = history[next];
        setUrl(u);
        setDraft(u);
        setIframeKey((k) => k + 1);
        if (mode === "reader") fetchReader(u);
        else setLoading(true);
    };
    const goForward = () => {
        if (historyIdx >= history.length - 1) return;
        const next = historyIdx + 1;
        setHistoryIdx(next);
        const u = history[next];
        setUrl(u);
        setDraft(u);
        setIframeKey((k) => k + 1);
        if (mode === "reader") fetchReader(u);
        else setLoading(true);
    };
    const reload = () => {
        if (!url) return;
        setIframeKey((k) => k + 1);
        if (mode === "reader") fetchReader(url);
        else setLoading(true);
    };

    // Switch mode while on the same page — fetch reader data lazily.
    useEffect(() => {
        if (mode === "reader" && url && !readerPage) fetchReader(url);
    }, [mode, url, readerPage, fetchReader]);

    const host = (() => {
        try {
            return url ? new URL(url).hostname : "";
        } catch (_e) {
            return "";
        }
    })();

    return (
        <div className="w-full h-full flex flex-col text-white" data-testid="browser-screen">
            {/* Top chrome */}
            <div className="px-3 py-2 border-b border-white/10 flex items-center gap-2">
                <Globe size={13} className="text-[#00F0FF]" />
                <button
                    onClick={goBack}
                    disabled={historyIdx <= 0}
                    data-testid="browser-back"
                    className="p-1 border border-white/10 hover:border-[#00F0FF]/60 hover:text-[#00F0FF] disabled:opacity-30"
                    aria-label="back"
                >
                    <ArrowLeft size={12} />
                </button>
                <button
                    onClick={goForward}
                    disabled={historyIdx >= history.length - 1}
                    data-testid="browser-forward"
                    className="p-1 border border-white/10 hover:border-[#00F0FF]/60 hover:text-[#00F0FF] disabled:opacity-30"
                    aria-label="forward"
                >
                    <ArrowRight size={12} />
                </button>
                <button
                    onClick={reload}
                    data-testid="browser-reload"
                    className="p-1 border border-white/10 hover:border-[#00F0FF]/60 hover:text-[#00F0FF]"
                    aria-label="reload"
                >
                    {loading ? (
                        <Loader2 size={12} className="animate-spin" />
                    ) : (
                        <RotateCw size={12} />
                    )}
                </button>
                <button
                    onClick={() => {
                        setUrl("");
                        setReaderPage(null);
                        setDraft("");
                    }}
                    data-testid="browser-home"
                    className="p-1 border border-white/10 hover:border-[#00F0FF]/60 hover:text-[#00F0FF]"
                    aria-label="home"
                >
                    <Home size={12} />
                </button>
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        navigate(draft);
                    }}
                    className="flex-1 flex items-center gap-2"
                >
                    <Shield size={11} className={url ? "text-[#CCFF00]" : "text-[#666]"} />
                    <input
                        ref={inputRef}
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        placeholder="paste any URL or search — althea proxies the response so frame-blocking sites still render"
                        className="flex-1 bg-transparent border border-white/10 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#00F0FF]/60"
                        data-testid="browser-url-input"
                        spellCheck={false}
                    />
                    {host && (
                        <span
                            className="label text-[9px] text-[#666] hidden md:inline"
                            title={url}
                        >
                            {host}
                        </span>
                    )}
                </form>
                {url && (
                    <span
                        className={`label text-[9px] px-1.5 py-0.5 hidden md:inline ${
                            isDirectEmbed
                                ? "text-[#FF2A88] border border-[#FF2A88]/40"
                                : "text-[#CCFF00] border border-[#CCFF00]/40"
                        }`}
                        title={
                            isDirectEmbed
                                ? "direct embed (no proxy needed)"
                                : "served via althea surf-proxy"
                        }
                        data-testid="browser-route-badge"
                    >
                        {isDirectEmbed ? "direct" : "proxy"}
                    </span>
                )}
                <Search size={11} className="text-[#666]" />
                <button
                    onClick={() => navigate(draft)}
                    data-testid="browser-go"
                    className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#00F0FF]/60 text-[#00F0FF] hover:bg-[#00F0FF]/10"
                >
                    surf
                </button>

                {/* Mode toggle */}
                <div className="flex border border-white/10 ml-1">
                    <button
                        onClick={() => setMode("live")}
                        data-testid="browser-mode-live"
                        className={`px-2 py-1 heading text-[9px] uppercase tracking-widest flex items-center gap-1 ${
                            mode === "live"
                                ? "bg-[#00F0FF]/15 text-[#00F0FF]"
                                : "text-[#888] hover:text-white"
                        }`}
                        title="render the live site through althea's proxy"
                    >
                        <Monitor size={10} /> live
                    </button>
                    <button
                        onClick={() => setMode("reader")}
                        data-testid="browser-mode-reader"
                        className={`px-2 py-1 heading text-[9px] uppercase tracking-widest flex items-center gap-1 ${
                            mode === "reader"
                                ? "bg-[#CCFF00]/15 text-[#CCFF00]"
                                : "text-[#888] hover:text-white"
                        }`}
                        title="extract title/text/links (works on any site)"
                    >
                        <BookOpen size={10} /> reader
                    </button>
                </div>

                {url && (
                    <button
                        onClick={() => onWatch?.(url)}
                        title="open in observation iframe"
                        data-testid="browser-to-observe"
                        className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-white/10 hover:border-[#CCFF00]/60 hover:text-[#CCFF00]"
                    >
                        <ExternalLink size={11} />
                    </button>
                )}
            </div>

            {/* Main viewport */}
            <div className="flex-1 relative min-h-0 bg-[#080808]">
                {!url && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center px-6 text-center">
                        <div className="label text-[#00F0FF] mb-2">browser idle</div>
                        <div className="text-[11px] text-white/70 max-w-lg mb-5 leading-relaxed">
                            paste any URL — althea proxies it server-side, strips
                            frame-blocking headers, and rewrites every asset so
                            the page renders inside her viewport. youtube watch
                            links auto-upgrade to embed players.
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-w-xl w-full">
                            {HOME_TARGETS.map((t) => (
                                <button
                                    key={t.url}
                                    onClick={() => navigate(t.url)}
                                    data-testid={`browser-bookmark-${t.label.replace(/\W+/g, "-")}`}
                                    className="text-left px-3 py-2 border border-white/10 hover:border-[#00F0FF]/60 hover:bg-[#00F0FF]/5"
                                >
                                    <div className="label text-[9px] text-[#00F0FF]">
                                        bookmark
                                    </div>
                                    <div className="text-[11px] text-white truncate">
                                        {t.label}
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {url && mode === "live" && (
                    <iframe
                        key={iframeKey}
                        src={proxySrc}
                        title="althea-browser"
                        className="absolute inset-0 w-full h-full bg-white"
                        sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-presentation allow-downloads allow-modals"
                        referrerPolicy="origin-when-cross-origin"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; fullscreen; gyroscope; picture-in-picture; web-share"
                        onLoad={onIframeLoad}
                        data-testid="browser-iframe"
                    />
                )}

                {url && mode === "reader" && (
                    <div className="absolute inset-0 grid grid-cols-1 lg:grid-cols-4 min-h-0">
                        <div className="lg:col-span-3 overflow-y-auto althea-scroll p-4">
                            {!readerPage && (
                                <div className="text-[11px] text-[#666]">
                                    extracting page…
                                </div>
                            )}
                            {readerPage && (
                                <div className="space-y-3" data-testid="browser-reader-page">
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <span className="label text-[9px] uppercase text-[#CCFF00]">
                                            {readerPage.status === 0
                                                ? "FAILED"
                                                : `HTTP ${readerPage.status}`}
                                        </span>
                                        {readerPage.host && (
                                            <span className="label text-[9px] uppercase text-[#666]">
                                                host · {readerPage.host}
                                            </span>
                                        )}
                                        {readerPage.title && (
                                            <h3 className="heading text-sm uppercase tracking-widest text-white">
                                                {readerPage.title}
                                            </h3>
                                        )}
                                    </div>
                                    {readerPage.error && (
                                        <div className="text-[11px] text-[#FF2A2A] border border-[#FF2A2A]/40 p-2">
                                            {readerPage.error}
                                        </div>
                                    )}
                                    <pre
                                        className="text-[11px] text-white/85 leading-relaxed whitespace-pre-wrap font-mono"
                                        data-testid="browser-reader-content"
                                    >
                                        {readerPage.text || "(no extractable text)"}
                                    </pre>
                                </div>
                            )}
                        </div>
                        <div className="overflow-y-auto althea-scroll p-3 space-y-1 border-l border-white/10 bg-[#050505]">
                            <div className="label text-[9px] uppercase tracking-widest text-[#CCFF00] mb-2">
                                link-graph
                            </div>
                            {!readerPage?.links?.length && (
                                <div className="text-[10px] text-[#555]">
                                    no links extracted.
                                </div>
                            )}
                            {(readerPage?.links || []).map((l, i) => (
                                <button
                                    key={`${l.url}|${i}`}
                                    onClick={() => navigate(l.url)}
                                    className="block text-left w-full text-[10px] text-white/70 hover:text-[#00F0FF] hover:bg-[#00F0FF]/5 border border-transparent hover:border-[#00F0FF]/20 px-2 py-1 truncate"
                                    data-testid={`browser-reader-link-${i}`}
                                    title={l.url}
                                >
                                    <span className="text-[#666] mr-1">›</span>
                                    {l.label}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Loading veil */}
                {loading && url && (
                    <div className="absolute top-2 left-2 z-10 flex items-center gap-2 px-2 py-1 bg-black/70 backdrop-blur border border-white/10 pointer-events-none">
                        <Loader2 size={12} className="animate-spin text-[#00F0FF]" />
                        <span className="label text-[9px] text-[#00F0FF]">
                            fetching · {host || "…"}
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
};

export default BrowserScreen;
