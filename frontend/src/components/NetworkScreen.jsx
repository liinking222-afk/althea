import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";

const TYPE_COLORS = {
    core: "#FFFFFF",
    peripheral: "#00F0FF",
    cognitive: "#CCFF00",
    host: "#FFAA00",
    reflection: "#A0A0FF",
};

const TYPE_RADIUS = {
    core: 0,
    peripheral: 110,
    cognitive: 190,
    host: 280,
    reflection: 360,
};

const NetworkScreen = ({ onHostClick, onCognitiveNodeClick }) => {
    const [graph, setGraph] = useState(null);
    const [hover, setHover] = useState(null);
    const [bridging, setBridging] = useState(false);
    const [bridgeInput, setBridgeInput] = useState("");
    const [bridgeResult, setBridgeResult] = useState(null);

    const refresh = useCallback(async () => {
        try {
            const res = await axios.get(`${API}/network/graph`);
            setGraph(res.data);
        } catch (error) {
            console.warn("network graph load failed:", error);
        }
    }, []);

    useEffect(() => {
        refresh();
        const t = setInterval(refresh, 6000);
        return () => clearInterval(t);
    }, [refresh]);

    const triggerBridge = async (e) => {
        e?.preventDefault?.();
        const url = bridgeInput.trim();
        if (!url || bridging) return;
        setBridging(true);
        setBridgeResult(null);
        try {
            const res = await axios.post(`${API}/bridge/web`, { url });
            setBridgeResult(res.data);
            await refresh();
        } catch (error) {
            setBridgeResult({
                host: "?",
                status: 0,
                title: null,
                description: `fetch failed: ${error.message}`,
            });
        } finally {
            setBridging(false);
        }
    };

    // Layout: ALTHEA core at center; type-grouped concentric rings.
    const positions = {};
    const counts = { peripheral: 0, cognitive: 0, host: 0, reflection: 0 };
    const groupCounts = { peripheral: 0, cognitive: 0, host: 0, reflection: 0 };

    if (graph) {
        graph.nodes.forEach((n) => {
            if (n.type !== "core") counts[n.type] = (counts[n.type] || 0) + 1;
        });
        graph.nodes.forEach((n) => {
            if (n.type === "core") {
                positions[n.id] = { x: 0, y: 0 };
                return;
            }
            const total = counts[n.type] || 1;
            const idx = groupCounts[n.type]++;
            const r = TYPE_RADIUS[n.type] ?? 200;
            const offset =
                n.type === "peripheral"
                    ? Math.PI
                    : n.type === "host"
                      ? 0
                      : -Math.PI / 2;
            const angle = offset + (idx / total) * Math.PI * 2;
            positions[n.id] = {
                x: Math.cos(angle) * r,
                y: Math.sin(angle) * r,
            };
        });
    }

    const W = 800;
    const H = 720;
    const cx = W / 2;
    const cy = H / 2;

    return (
        <div
            className="h-full flex flex-col relative"
            data-testid="network-screen"
        >
            <div className="px-4 py-2 border-b border-white/10 flex items-center gap-2">
                <form onSubmit={triggerBridge} className="flex-1 flex items-center gap-2">
                    <span className="label text-[#00F0FF] glow-cyan">bridge://</span>
                    <input
                        value={bridgeInput}
                        onChange={(e) => setBridgeInput(e.target.value)}
                        placeholder="fetch any url through althea's web bridge"
                        className="flex-1 bg-transparent outline-none text-[12px] font-mono text-white placeholder:text-[#444]"
                        data-testid="bridge-url-input"
                    />
                    <button
                        type="submit"
                        disabled={bridging}
                        data-testid="bridge-fetch-btn"
                        className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#00F0FF]/60 text-[#00F0FF] hover:bg-[#00F0FF]/10 disabled:opacity-40"
                    >
                        {bridging ? "fetching" : "bridge"}
                    </button>
                </form>
                <button
                    onClick={refresh}
                    data-testid="network-refresh-btn"
                    className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-white/15 hover:border-[#CCFF00]/60 hover:text-[#CCFF00]"
                >
                    refresh
                </button>
            </div>

            <div className="flex-1 relative min-h-0 overflow-hidden">
                <svg
                    viewBox={`-${W / 2} -${H / 2} ${W} ${H}`}
                    className="absolute inset-0 w-full h-full"
                    preserveAspectRatio="xMidYMid meet"
                    data-testid="network-graph-svg"
                >
                    {/* concentric rings */}
                    {Object.entries(TYPE_RADIUS)
                        .filter(([t]) => t !== "core")
                        .map(([t, r]) => (
                            <circle
                                key={t}
                                cx={0}
                                cy={0}
                                r={r}
                                fill="none"
                                stroke="rgba(255,255,255,0.05)"
                                strokeDasharray="2 4"
                            />
                        ))}

                    {/* edges */}
                    {graph?.edges?.map((e, i) => {
                        const a = positions[e.source];
                        const b = positions[e.target];
                        if (!a || !b) return null;
                        const color =
                            e.kind === "parent"
                                ? "#00F0FF"
                                : e.kind === "perceives"
                                  ? "#00F0FF"
                                  : e.kind === "observed"
                                    ? "#FFAA00"
                                    : "#CCFF00";
                        return (
                            <line
                                key={`e-${i}`}
                                x1={a.x}
                                y1={a.y}
                                x2={b.x}
                                y2={b.y}
                                stroke={color}
                                strokeOpacity="0.35"
                                strokeWidth={e.kind === "parent" ? 1.5 : 0.8}
                            />
                        );
                    })}

                    {/* nodes */}
                    {graph?.nodes?.map((n) => {
                        const p = positions[n.id];
                        if (!p) return null;
                        const color = TYPE_COLORS[n.type] || "#FFFFFF";
                        const r =
                            n.type === "core"
                                ? 14
                                : 5 + (n.weight || 1) * 1.5;
                        const handleClick = () => {
                            if (n.type === "host") {
                                // bridge fetch this host directly
                                setBridgeInput(`https://${n.label}/`);
                                setBridging(true);
                                setBridgeResult(null);
                                axios
                                    .post(`${API}/bridge/web`, {
                                        url: `https://${n.label}/`,
                                    })
                                    .then((res) => {
                                        setBridgeResult(res.data);
                                        refresh();
                                    })
                                    .catch((error) =>
                                        setBridgeResult({
                                            host: n.label,
                                            status: 0,
                                            title: null,
                                            description: `fetch failed: ${error.message}`,
                                        }),
                                    )
                                    .finally(() => setBridging(false));
                            } else if (n.type === "cognitive" && onCognitiveNodeClick) {
                                onCognitiveNodeClick(n.label);
                            }
                        };
                        return (
                            <g
                                key={n.id}
                                transform={`translate(${p.x},${p.y})`}
                                onMouseEnter={() => setHover(n)}
                                onMouseLeave={() => setHover(null)}
                                onClick={handleClick}
                                style={{
                                    cursor:
                                        n.type === "host" ||
                                        n.type === "cognitive"
                                            ? "pointer"
                                            : "default",
                                }}
                                data-testid={`network-node-${n.id}`}
                            >
                                {/* invisible larger picking circle for easier click */}
                                <circle r={Math.max(r + 4, 10)} fill="transparent" />
                                <circle
                                    r={r}
                                    fill={color}
                                    fillOpacity={n.type === "core" ? 0.9 : 0.85}
                                    stroke={color}
                                    strokeWidth={1}
                                    style={{
                                        filter: `drop-shadow(0 0 8px ${color}AA)`,
                                    }}
                                />
                                <text
                                    x={r + 4}
                                    y={3}
                                    fontSize={9}
                                    fill={color}
                                    fontFamily="JetBrains Mono, monospace"
                                    style={{ pointerEvents: "none" }}
                                >
                                    {n.label}
                                </text>
                            </g>
                        );
                    })}
                </svg>

                {/* legend */}
                <div className="absolute top-3 left-3 space-y-1 pointer-events-none">
                    <div className="label text-[9px] text-[#888]">legend</div>
                    {Object.entries(TYPE_COLORS).map(([t, c]) => (
                        <div key={t} className="flex items-center gap-2">
                            <span
                                className="inline-block w-2 h-2"
                                style={{ background: c, boxShadow: `0 0 6px ${c}` }}
                            />
                            <span className="text-[10px] text-white/70 heading uppercase tracking-widest">
                                {t}
                            </span>
                        </div>
                    ))}
                </div>

                {/* hover detail */}
                {hover && (
                    <div className="absolute bottom-3 left-3 right-3 max-w-2xl bg-black/80 backdrop-blur-sm border-l-2 border-[#CCFF00] p-3 fade-up pointer-events-none">
                        <div className="label text-[#CCFF00] mb-1">
                            {hover.type} // {hover.label}
                        </div>
                        <div className="text-[11px] text-white/80 break-words">
                            {hover.meta && Object.keys(hover.meta).length > 0
                                ? Object.entries(hover.meta)
                                      .map(([k, v]) => `${k}: ${v}`)
                                      .join(" · ")
                                : "no metadata"}
                        </div>
                    </div>
                )}

                {/* bridge result panel */}
                {bridgeResult && (
                    <div className="absolute top-3 right-3 max-w-md bg-black/85 backdrop-blur-sm border-l-2 border-[#00F0FF] p-3 fade-up">
                        <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                                <div className="label text-[#00F0FF] glow-cyan mb-1">
                                    bridge // {bridgeResult.host} · {bridgeResult.status}
                                </div>
                                {bridgeResult.title && (
                                    <div className="text-[12px] text-white font-bold mb-1 truncate">
                                        {bridgeResult.title}
                                    </div>
                                )}
                                {bridgeResult.description && (
                                    <div className="text-[11px] text-white/70 leading-relaxed">
                                        {bridgeResult.description.slice(0, 240)}
                                    </div>
                                )}
                                {bridgeResult.elapsed_ms !== undefined && (
                                    <div className="text-[10px] text-[#666] mt-2 heading uppercase tracking-widest">
                                        {bridgeResult.elapsed_ms}ms · {(bridgeResult.links || []).length} links
                                    </div>
                                )}
                            </div>
                            <button
                                onClick={() => setBridgeResult(null)}
                                className="text-[#888] hover:text-white text-[10px]"
                                data-testid="bridge-result-dismiss"
                            >
                                ×
                            </button>
                        </div>
                    </div>
                )}

                {/* empty state */}
                {graph && graph.nodes.length <= 1 && (
                    <div className="absolute inset-0 flex items-center justify-center text-center px-6 pointer-events-none">
                        <div>
                            <div className="label text-[#CCFF00] mb-2">
                                network silent
                            </div>
                            <div className="text-[12px] text-white/60 max-w-md">
                                grant a permission, watch a URL, spawn a lattice node, or use
                                the bridge above. interactions will start populating this graph.
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default NetworkScreen;
