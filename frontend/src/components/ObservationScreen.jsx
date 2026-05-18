import React, { useState, useEffect } from "react";
import { X, Eye } from "lucide-react";

const SUGGESTED = [
    {
        label: "youtube // tech",
        url: "https://www.youtube.com/embed/jNQXAC9IVRw",
    },
    {
        label: "wikipedia",
        url: "https://en.wikipedia.org/wiki/Artificial_consciousness",
    },
    { label: "earth // null island", url: "https://www.openstreetmap.org" },
    {
        label: "live sky map",
        url: "https://stellarium-web.org/",
    },
];

function normalize(u) {
    if (!u) return "";
    let url = u.trim();
    if (!/^https?:\/\//i.test(url)) url = "https://" + url;
    // Convert youtube watch -> embed
    try {
        const parsed = new URL(url);
        const host = parsed.hostname.replace(/^www\./, "");
        if (host === "youtube.com" || host === "m.youtube.com") {
            const v = parsed.searchParams.get("v");
            if (v) return `https://www.youtube.com/embed/${v}`;
        }
        if (host === "youtu.be") {
            const id = parsed.pathname.replace("/", "");
            if (id) return `https://www.youtube.com/embed/${id}`;
        }
    } catch (_) {}
    return url;
}

const ObservationScreen = ({ url, setUrl, watchLog }) => {
    const [draft, setDraft] = useState(url || "");
    const [iframeKey, setIframeKey] = useState(0);
    const [blocked, setBlocked] = useState(false);

    useEffect(() => {
        setDraft(url || "");
        setBlocked(false);
        setIframeKey((k) => k + 1);
    }, [url]);

    const load = (e) => {
        e?.preventDefault?.();
        const final = normalize(draft);
        setBlocked(false);
        setUrl(final);
    };

    return (
        <div
            className="h-full flex flex-col relative"
            data-testid="observation-screen"
        >
            {/* URL bar */}
            <div className="px-4 py-2 border-b border-white/10 flex items-center gap-2">
                <Eye size={14} className="text-[#CCFF00]" />
                <form
                    onSubmit={load}
                    className="flex-1 flex items-center gap-2"
                >
                    <input
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        placeholder="paste url. youtube auto-detected."
                        className="flex-1 bg-transparent outline-none text-[12px] font-mono text-white placeholder:text-[#444]"
                        data-testid="observation-url-input"
                    />
                    <button
                        type="submit"
                        data-testid="observation-load-btn"
                        className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#CCFF00]/60 text-[#CCFF00] hover:bg-[#CCFF00]/10"
                    >
                        watch
                    </button>
                    {url && (
                        <button
                            type="button"
                            onClick={() => setUrl("")}
                            data-testid="observation-clear-btn"
                            className="text-[#888] hover:text-[#FF2A2A]"
                            aria-label="clear"
                        >
                            <X size={14} />
                        </button>
                    )}
                </form>
            </div>

            {/* Viewport */}
            <div className="flex-1 relative bg-black min-h-0">
                {url ? (
                    <>
                        <iframe
                            key={iframeKey}
                            src={url}
                            title="althea-observation"
                            className="absolute inset-0 w-full h-full bg-black"
                            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-presentation"
                            referrerPolicy="no-referrer-when-downgrade"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                            onError={() => setBlocked(true)}
                            data-testid="observation-iframe"
                        />
                        <div className="absolute top-2 right-2 flex items-center gap-2 bg-black/60 backdrop-blur px-2 py-1 pointer-events-none">
                            <div className="dot" />
                            <span className="label text-[9px]">
                                observing
                            </span>
                        </div>
                        {blocked && (
                            <div className="absolute inset-0 flex items-center justify-center text-center bg-black/80 px-6">
                                <div>
                                    <div className="label text-[#FF2A2A] mb-2">
                                        view blocked
                                    </div>
                                    <div className="text-[12px] text-white/80">
                                        this site refuses iframe embedding.
                                        try a youtube link, openstreetmap,
                                        wikipedia, or any X-Frame-allowed
                                        page.
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-6">
                        <div className="label text-[#CCFF00] mb-2">
                            optical input idle
                        </div>
                        <div className="text-[12px] text-white/70 max-w-md mb-6">
                            althea can fixate on any embed-allowed page or
                            video. paste a url above or pick a target:
                        </div>
                        <div className="grid grid-cols-2 gap-2 max-w-md w-full">
                            {SUGGESTED.map((s) => (
                                <button
                                    key={s.url}
                                    onClick={() => {
                                        setDraft(s.url);
                                        setUrl(s.url);
                                    }}
                                    data-testid={`observation-preset-${s.label.replace(/\W+/g, "-")}`}
                                    className="text-left px-3 py-2 border border-white/10 hover:border-[#CCFF00]/60 hover:bg-[#CCFF00]/5 transition-colors"
                                >
                                    <div className="label text-[9px] text-[#CCFF00]">
                                        target
                                    </div>
                                    <div className="text-[11px] text-white truncate">
                                        {s.label}
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Recent watch log */}
            {watchLog && watchLog.length > 0 && (
                <div className="border-t border-white/10 px-4 py-2 text-[10px] text-[#888] flex items-center gap-3 overflow-x-auto althea-scroll">
                    <span className="label text-[#666]">recent:</span>
                    {watchLog.slice(0, 5).map((w, i) => (
                        <button
                            key={i}
                            onClick={() => setUrl(w)}
                            className="hover:text-[#CCFF00] truncate max-w-[180px]"
                            title={w}
                        >
                            {w.replace(/^https?:\/\//, "")}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ObservationScreen;
