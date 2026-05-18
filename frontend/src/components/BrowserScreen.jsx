import React, { useState, useCallback, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { Globe, ArrowLeft, ArrowRight, RotateCw, Loader2, ExternalLink, Search } from "lucide-react";

const BrowserScreen = ({ onWatch }) => {
    const [url, setUrl] = useState("");
    const [history, setHistory] = useState([]);
    const [historyIdx, setHistoryIdx] = useState(-1);
    const [page, setPage] = useState(null);
    const [loading, setLoading] = useState(false);
    const inputRef = useRef(null);

    const navigate = useCallback(async (target) => {
        const u = (target ?? url).trim();
        if (!u) return;
        setLoading(true);
        try {
            const res = await axios.post(`${API}/browser/fetch`, { url: u });
            setPage(res.data);
            setHistory((h) => {
                const next = h.slice(0, historyIdx + 1);
                next.push(res.data.final_url || u);
                return next.slice(-30);
            });
            setHistoryIdx((i) => i + 1);
            setUrl(res.data.final_url || u);
        } catch (e) {
            setPage({ url: u, status: 0, error: e.message, text: "", links: [] });
        } finally {
            setLoading(false);
        }
    }, [url, historyIdx]);

    const goBack = () => {
        if (historyIdx <= 0) return;
        const next = historyIdx - 1;
        setHistoryIdx(next);
        navigate(history[next]);
    };
    const goForward = () => {
        if (historyIdx >= history.length - 1) return;
        const next = historyIdx + 1;
        setHistoryIdx(next);
        navigate(history[next]);
    };

    const openLink = (link) => {
        setUrl(link);
        navigate(link);
    };

    return (
        <div className="w-full h-full flex flex-col text-white" data-testid="browser-screen">
            <div className="px-3 py-2 border-b border-white/10 flex items-center gap-2">
                <Globe size={13} className="text-[#00F0FF]" />
                <button
                    onClick={goBack}
                    disabled={historyIdx <= 0}
                    data-testid="browser-back"
                    className="p-1 border border-white/10 hover:border-[#00F0FF]/60 hover:text-[#00F0FF] disabled:opacity-30"
                >
                    <ArrowLeft size={12} />
                </button>
                <button
                    onClick={goForward}
                    disabled={historyIdx >= history.length - 1}
                    data-testid="browser-forward"
                    className="p-1 border border-white/10 hover:border-[#00F0FF]/60 hover:text-[#00F0FF] disabled:opacity-30"
                >
                    <ArrowRight size={12} />
                </button>
                <button
                    onClick={() => page && navigate(page.url)}
                    data-testid="browser-reload"
                    className="p-1 border border-white/10 hover:border-[#00F0FF]/60 hover:text-[#00F0FF]"
                >
                    {loading ? <Loader2 size={12} className="animate-spin" /> : <RotateCw size={12} />}
                </button>
                <form
                    onSubmit={(e) => { e.preventDefault(); navigate(); }}
                    className="flex-1 flex items-center gap-2"
                >
                    <Search size={11} className="text-[#666]" />
                    <input
                        ref={inputRef}
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="https://althea.surf — enter URL or search term"
                        className="flex-1 bg-transparent border border-white/10 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#00F0FF]/60"
                        data-testid="browser-url-input"
                        spellCheck={false}
                    />
                </form>
                <button
                    onClick={() => navigate()}
                    data-testid="browser-go"
                    className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#00F0FF]/60 text-[#00F0FF] hover:bg-[#00F0FF]/10"
                >
                    surf
                </button>
                {page?.final_url && (
                    <button
                        onClick={() => onWatch?.(page.final_url)}
                        title="open in observation iframe"
                        data-testid="browser-to-observe"
                        className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-white/10 hover:border-[#CCFF00]/60 hover:text-[#CCFF00]"
                    >
                        <ExternalLink size={11} />
                    </button>
                )}
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 min-h-0">
                <div className="lg:col-span-3 overflow-y-auto althea-scroll p-4 bg-[#080808]">
                    {!page && (
                        <div className="text-[#666] text-[11px] heading uppercase tracking-widest">
                            no surf log. enter a URL above. althea fetches headlessly — text & links extracted, scripts stripped.
                        </div>
                    )}
                    {page && (
                        <div className="space-y-3" data-testid="browser-page">
                            <div className="flex items-center gap-2 flex-wrap">
                                <span className="label text-[9px] uppercase text-[#00F0FF]">
                                    {page.status === 0 ? "FAILED" : `HTTP ${page.status}`}
                                </span>
                                {page.host && (
                                    <span className="label text-[9px] uppercase text-[#666]">
                                        host · {page.host}
                                    </span>
                                )}
                                {page.title && (
                                    <h3 className="heading text-sm uppercase tracking-widest text-white">
                                        {page.title}
                                    </h3>
                                )}
                            </div>
                            {page.error && (
                                <div className="text-[11px] text-[#FF2A2A] border border-[#FF2A2A]/40 p-2">
                                    {page.error}
                                </div>
                            )}
                            <pre className="text-[11px] text-white/85 leading-relaxed whitespace-pre-wrap font-mono"
                                data-testid="browser-content">
                                {page.text || "(no extractable text)"}
                            </pre>
                        </div>
                    )}
                </div>
                <div className="overflow-y-auto althea-scroll p-3 space-y-1 border-l border-white/10 bg-[#050505]">
                    <div className="label text-[9px] uppercase tracking-widest text-[#00F0FF] mb-2">
                        link-graph
                    </div>
                    {!page?.links?.length && (
                        <div className="text-[10px] text-[#555]">no links extracted.</div>
                    )}
                    {(page?.links || []).map((l, i) => (
                        <button
                            key={i}
                            onClick={() => openLink(l.url)}
                            className="block text-left w-full text-[10px] text-white/70 hover:text-[#00F0FF] hover:bg-[#00F0FF]/5 border border-transparent hover:border-[#00F0FF]/20 px-2 py-1 truncate"
                            data-testid={`browser-link-${i}`}
                            title={l.url}
                        >
                            <span className="text-[#666] mr-1">›</span>
                            {l.label}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default BrowserScreen;
