// ResearchScreen — ARTM/1.0 autonomous research substrate.
// Spawn parallel research threads, watch them cross-reference sources live,
// and see the persistent symbolic memory graph grow.
import React, { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { Brain, Loader2, Radar, GitBranch, ExternalLink } from "lucide-react";
import GraphExplorerPanel from "@/components/GraphExplorerPanel";

const V = "#A29BFE";
const LIME = "#CCFF00";
const CYAN = "#00E5FF";

const SymbolicGraph = ({ graph, onPick }) => {
    const ref = useRef(null);
    const hitsRef = useRef([]);
    useEffect(() => {
        const cv = ref.current;
        if (!cv) return;
        const ctx = cv.getContext("2d");
        const W = (cv.width = cv.clientWidth * 2);
        const H = (cv.height = cv.clientHeight * 2);
        ctx.clearRect(0, 0, W, H);
        ctx.fillStyle = "#050507";
        ctx.fillRect(0, 0, W, H);
        hitsRef.current = [];
        const nodes = (graph?.nodes || []).slice(0, 40);
        if (!nodes.length) {
            ctx.fillStyle = "#555";
            ctx.font = "22px monospace";
            ctx.fillText("no concepts yet — spawn a research thread", 40, H / 2);
            return;
        }
        const cx = W / 2, cy = H / 2;
        const R = Math.min(W, H) * 0.38;
        const pos = {};
        nodes.forEach((n, i) => {
            const a = (i / nodes.length) * Math.PI * 2;
            const rad = R * (0.55 + 0.45 * ((n.weight % 5) / 5));
            pos[n.id] = { x: cx + rad * Math.cos(a), y: cy + rad * Math.sin(a), n };
        });
        // edges
        (graph.edges || []).forEach((e) => {
            const a = pos[e.source], b = pos[e.target];
            if (!a || !b) return;
            ctx.strokeStyle = `rgba(162,155,254,${Math.min(0.15 + e.strength * 0.1, 0.7)})`;
            ctx.lineWidth = Math.min(0.6 + e.strength * 0.5, 3);
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
        });
        // nodes
        Object.values(pos).forEach(({ x, y, n }) => {
            const r = 5 + Math.min(n.weight * 2.5, 22);
            hitsRef.current.push({ x, y, r, id: n.id, concept: n.concept });
            const g = ctx.createRadialGradient(x, y, 0, x, y, r);
            g.addColorStop(0, "#CCFF00");
            g.addColorStop(1, "rgba(162,155,254,0.15)");
            ctx.fillStyle = g;
            ctx.beginPath();
            ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = "#dfe";
            ctx.font = "20px monospace";
            ctx.fillText(String(n.concept).slice(0, 22), x + r + 4, y + 6);
        });
    }, [graph]);
    const onClick = (e) => {
        const cv = ref.current;
        if (!cv || !onPick) return;
        const rect = cv.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * cv.width;
        const y = ((e.clientY - rect.top) / rect.height) * cv.height;
        let best = null;
        for (const h of hitsRef.current) {
            const d = Math.hypot(h.x - x, h.y - y);
            if (d <= h.r + 14 && (!best || d < best.d)) best = { ...h, d };
        }
        if (best) onPick(best.id, best.concept);
    };
    return (
        <canvas
            ref={ref}
            onClick={onClick}
            className="w-full h-full block cursor-pointer"
            data-testid="symbolic-graph-canvas"
        />
    );
};

export default function ResearchScreen() {
    const [threads, setThreads] = useState([]);
    const [active, setActive] = useState([]);
    const [graph, setGraph] = useState(null);
    const [query, setQuery] = useState("");
    const [busy, setBusy] = useState(false);
    const [open, setOpen] = useState(null);
    const [sel, setSel] = useState(null);

    const refresh = useCallback(async () => {
        try {
            const [t, g] = await Promise.all([
                axios.get(`${API}/research/threads?limit=15`),
                axios.get(`${API}/research/graph`),
            ]);
            setThreads(t.data.threads || []);
            setActive(t.data.active || []);
            setGraph(g.data);
        } catch (e) { /* transient */ }
    }, []);

    useEffect(() => {
        refresh();
        const i = setInterval(refresh, 4000);
        return () => clearInterval(i);
    }, [refresh]);

    const spawn = async () => {
        if (!query.trim() || busy) return;
        setBusy(true);
        try {
            await axios.post(`${API}/research/spawn`, { query: query.trim(), priority: 8 });
            setQuery("");
            setTimeout(refresh, 800);
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="h-full flex flex-col overflow-hidden" data-testid="research-screen">
            <div className="px-3 py-2 border-b border-white/10 flex items-center gap-2 flex-wrap">
                <Brain size={14} style={{ color: V }} />
                <span className="heading text-[10px] uppercase tracking-widest" style={{ color: V }}>
                    ARTM/1.0
                </span>
                <span className="text-[9px] font-mono text-[#888]">
                    parallel research · cross-reference · symbolic memory graph
                </span>
                <span className="ml-auto text-[9px] font-mono" style={{ color: active.length ? LIME : "#666" }}>
                    {active.length} thread{active.length === 1 ? "" : "s"} active
                </span>
            </div>

            <div className="px-3 py-2 border-b border-white/10 flex gap-2">
                <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && spawn()}
                    placeholder="research a topic — e.g. fusion energy breakthroughs 2026"
                    data-testid="research-input"
                    className="flex-1 bg-transparent border border-white/10 px-2 py-1.5 text-[12px] font-mono outline-none focus:border-[#A29BFE]/60 text-white placeholder:text-[#555]"
                />
                <button
                    onClick={spawn}
                    disabled={busy || !query.trim()}
                    data-testid="research-spawn-btn"
                    className="heading text-[10px] uppercase tracking-widest px-3 py-1.5 border border-[#A29BFE]/50 text-[#A29BFE] hover:bg-[#A29BFE]/10 disabled:opacity-40 flex items-center gap-1"
                >
                    {busy ? <Loader2 size={11} className="animate-spin" /> : <Radar size={11} />} spawn
                </button>
            </div>

            <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-2 gap-0">
                {/* threads */}
                <div className="min-h-0 overflow-y-auto althea-scroll border-r border-white/10 p-2 space-y-2">
                    {threads.length === 0 && (
                        <div className="text-[11px] font-mono text-[#666] p-3">
                            no research threads yet — spawn one above or say "research X" in the terminal.
                        </div>
                    )}
                    {threads.map((t) => (
                        <div
                            key={t.thread_id}
                            onClick={() => setOpen(open === t.thread_id ? null : t.thread_id)}
                            data-testid={`research-thread-${t.status}`}
                            className="border border-white/10 hover:border-[#A29BFE]/40 p-2 cursor-pointer"
                        >
                            <div className="flex items-center gap-2">
                                <span
                                    className="label text-[8px] px-1 py-0.5 uppercase tracking-widest"
                                    style={{
                                        color: t.status === "ACTIVE" ? LIME
                                            : t.status === "COMPLETE" ? CYAN : "#FF2A2A",
                                        borderColor: "currentColor",
                                        borderWidth: 1,
                                    }}
                                >
                                    {t.status === "ACTIVE" ? "◉ active" : t.status.toLowerCase()}
                                </span>
                                <span className="text-[11px] text-white/85 truncate flex-1">{t.query}</span>
                                <span className="text-[9px] font-mono text-[#888]">
                                    d{t.depth} · {Math.round((t.confidence || 0) * 100)}%
                                </span>
                            </div>
                            <div className="text-[9px] font-mono text-[#777] mt-1 flex gap-3">
                                <span>{(t.findings || []).length} findings</span>
                                <span>{(t.cross_refs || []).length} corroborated</span>
                                <span>{(t.concepts || []).length} concepts</span>
                            </div>
                            {open === t.thread_id && (
                                <div className="mt-2 space-y-1.5 border-t border-white/10 pt-2">
                                    {(t.concepts || []).length > 0 && (
                                        <div className="flex flex-wrap gap-1">
                                            {t.concepts.map((c) => (
                                                <span key={c} className="text-[9px] px-1.5 py-0.5 border border-[#A29BFE]/30 text-[#A29BFE]">
                                                    {c}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                    {(t.findings || []).slice(0, 4).map((f, i) => (
                                        <a
                                            key={i}
                                            href={f.url}
                                            target="_blank"
                                            rel="noreferrer"
                                            onClick={(e) => e.stopPropagation()}
                                            className="block text-[10px] text-[#9fb] hover:text-[#CCFF00]"
                                        >
                                            <ExternalLink size={9} className="inline mr-1" />
                                            {f.title || f.url}
                                        </a>
                                    ))}
                                    {(t.cross_refs || []).slice(0, 2).map((x, i) => (
                                        <div key={i} className="text-[9px] text-[#888] italic">
                                            ✓ {x.claim?.slice(0, 120)}
                                            <span className="text-[#A29BFE]"> [{(x.corroborated_by || []).join(", ")}]</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {/* symbolic graph */}
                <div className="min-h-[240px] relative">
                    <div className="absolute top-2 left-2 z-10 flex items-center gap-1.5 pointer-events-none">
                        <GitBranch size={11} style={{ color: V }} />
                        <span className="label text-[9px] uppercase tracking-widest text-[#888]">
                            symbolic memory graph · {graph?.count || 0} concepts — click a node to explore
                        </span>
                    </div>
                    <SymbolicGraph
                        graph={graph}
                        onPick={(id, concept) => setSel({ id, concept })}
                    />
                    {sel && (
                        <div className="absolute inset-y-2 right-2 w-72 max-w-[90%] z-20">
                            <GraphExplorerPanel
                                nodeId={sel.id}
                                onSelect={(id, concept) => setSel({ id, concept })}
                                onClose={() => setSel(null)}
                            />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
