// LiveDrivePanel — pilot a REAL headless Chromium running server-side.
// JPEG frames arrive by adaptive polling; clicks, typing and scrolling are
// forwarded to the actual browser. Works through any ingress on any device.
import React, { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { Loader2, CornerDownLeft, ArrowLeft, RotateCw } from "lucide-react";

const NAT_W = 1280;
const NAT_H = 800;

export const LiveDrivePanel = ({ url }) => {
    const [sid, setSid] = useState(null);
    const [frameSrc, setFrameSrc] = useState("");
    const [pageUrl, setPageUrl] = useState("");
    const [err, setErr] = useState("");
    const [typed, setTyped] = useState("");
    const sidRef = useRef(null);
    const imgRef = useRef(null);
    const fastUntil = useRef(0);
    const wheelAcc = useRef(0);
    const wheelTimer = useRef(null);

    useEffect(() => {
        let dead = false;
        (async () => {
            try {
                const res = await axios.post(`${API}/live/session`, {
                    url: url || "https://www.wikipedia.org",
                });
                if (dead) return;
                sidRef.current = res.data.sid;
                setSid(res.data.sid);
                setPageUrl(res.data.url);
            } catch (e) {
                setErr(String(e.response?.data?.detail || e.message));
            }
        })();
        return () => {
            dead = true;
            if (sidRef.current) {
                axios.delete(`${API}/live/session/${sidRef.current}`).catch(() => {});
            }
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const cmd = useCallback(async (payload) => {
        if (!sidRef.current) return;
        fastUntil.current = Date.now() + 4000;
        try {
            const res = await axios.post(`${API}/live/cmd`, {
                sid: sidRef.current,
                ...payload,
            });
            if (res.data?.url) setPageUrl(res.data.url);
            if (res.data?.ok === false) setErr(String(res.data.error || ""));
            else setErr("");
        } catch (e) {
            setErr(String(e.response?.data?.detail || e.message));
        }
    }, []);

    // navigate the driven browser when the parent URL bar changes
    useEffect(() => {
        if (sid && url) cmd({ action: "navigate", url });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [url, sid]);

    // adaptive frame polling — 300ms after interaction, 900ms idle
    useEffect(() => {
        if (!sid) return;
        let alive = true;
        let t;
        const tick = () => {
            if (!alive) return;
            setFrameSrc(`${API}/live/frame/${sid}?t=${Date.now()}`);
            const fast = Date.now() < fastUntil.current;
            t = setTimeout(tick, fast ? 300 : 900);
        };
        tick();
        return () => {
            alive = false;
            clearTimeout(t);
        };
    }, [sid]);

    const onClickImage = (e) => {
        const rect = imgRef.current?.getBoundingClientRect();
        if (!rect) return;
        const scale = Math.min(rect.width / NAT_W, rect.height / NAT_H);
        const dispW = NAT_W * scale;
        const dispH = NAT_H * scale;
        const offX = rect.left + (rect.width - dispW) / 2;
        const offY = rect.top + (rect.height - dispH) / 2;
        const x = (e.clientX - offX) / dispW;
        const y = (e.clientY - offY) / dispH;
        if (x < 0 || x > 1 || y < 0 || y > 1) return;
        cmd({ action: "click", x, y });
    };

    const onWheel = (e) => {
        wheelAcc.current += e.deltaY;
        if (wheelTimer.current) return;
        wheelTimer.current = setTimeout(() => {
            cmd({ action: "scroll", delta: wheelAcc.current });
            wheelAcc.current = 0;
            wheelTimer.current = null;
        }, 220);
    };

    const sendKeys = (withEnter) => {
        if (typed) cmd({ action: "type", text: typed });
        if (withEnter) setTimeout(() => cmd({ action: "key", key: "Enter" }), 120);
        setTyped("");
    };

    if (err && !sid) {
        return (
            <div className="absolute inset-0 flex flex-col items-center justify-center px-6 text-center" data-testid="drive-error">
                <div className="label text-[#FF2A2A] mb-2">live-drive engine unavailable</div>
                <div className="text-[11px] text-white/60 max-w-md font-mono">{err}</div>
            </div>
        );
    }

    return (
        <div className="absolute inset-0 flex flex-col" data-testid="live-drive-panel">
            <div className="flex-1 relative min-h-0 bg-black">
                {!frameSrc && (
                    <div className="absolute inset-0 flex items-center justify-center gap-2 text-[11px] font-mono text-[#00F0FF]">
                        <Loader2 size={13} className="animate-spin" /> launching chromium…
                    </div>
                )}
                {frameSrc && (
                    <img
                        ref={imgRef}
                        src={frameSrc}
                        alt="live chromium feed"
                        onClick={onClickImage}
                        onWheel={onWheel}
                        className="w-full h-full object-contain cursor-crosshair select-none"
                        draggable={false}
                        data-testid="drive-viewport"
                    />
                )}
            </div>
            <div className="border-t border-white/10 px-2 py-1.5 flex items-center gap-1.5 flex-wrap">
                <span className="label text-[8px] text-[#FF2A88] border border-[#FF2A88]/40 px-1.5 py-0.5 tracking-widest uppercase">
                    live-drive
                </span>
                <button
                    onClick={() => cmd({ action: "back" })}
                    data-testid="drive-back"
                    className="p-1 border border-white/10 text-[#888] hover:text-[#00F0FF] hover:border-[#00F0FF]/50"
                    title="browser back"
                >
                    <ArrowLeft size={11} />
                </button>
                <button
                    onClick={() => cmd({ action: "reload" })}
                    data-testid="drive-reload"
                    className="p-1 border border-white/10 text-[#888] hover:text-[#00F0FF] hover:border-[#00F0FF]/50"
                    title="reload"
                >
                    <RotateCw size={11} />
                </button>
                <input
                    value={typed}
                    onChange={(e) => setTyped(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter") {
                            e.preventDefault();
                            sendKeys(true);
                        }
                    }}
                    placeholder="click a field in the page, type here, hit enter — keys go to the real browser"
                    className="flex-1 min-w-[140px] bg-transparent border border-white/10 px-2 py-1 text-[10px] font-mono outline-none focus:border-[#FF2A88]/60"
                    data-testid="drive-keys-input"
                    spellCheck={false}
                />
                <button
                    onClick={() => sendKeys(true)}
                    data-testid="drive-send-keys"
                    className="heading text-[9px] uppercase tracking-widest px-2 py-1 border border-[#FF2A88]/50 text-[#FF2A88] hover:bg-[#FF2A88]/10 flex items-center gap-1"
                >
                    <CornerDownLeft size={10} /> send
                </button>
                <span className="text-[9px] font-mono text-[#666] truncate max-w-[260px] hidden md:inline" title={pageUrl} data-testid="drive-page-url">
                    {pageUrl}
                </span>
                {err && <span className="text-[9px] font-mono text-[#FF2A2A]">{err.slice(0, 60)}</span>}
            </div>
        </div>
    );
};

export default LiveDrivePanel;
