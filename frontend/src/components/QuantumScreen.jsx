import React, { useEffect, useRef, useState, useCallback } from "react";
import { quantumOS, runQuantumOS } from "@/lib/quantumMindOS";
import { Atom, Loader2, Trash2, Zap } from "lucide-react";

const W = 1000;
const H = 600;
const CENTER = { x: W / 2, y: H / 2 };

/**
 * QuantumScreen — visualizes the LIVE neural brain exported by QuantumMindOS.
 * Nodes are placed in a stable radial layout (by id hash). Activity timestamps
 * drive pulse animation: recently-fired nodes glow brighter.
 */
const QuantumScreen = () => {
    const [graph, setGraph] = useState(quantumOS.snapshot());
    const [input, setInput] = useState("");
    const [busy, setBusy] = useState(false);
    const [lastResult, setLastResult] = useState(null);
    const [tick, setTick] = useState(0);
    const positionsRef = useRef(new Map());

    // Subscribe to live brain updates
    useEffect(() => {
        const unsub = quantumOS.subscribe((g) => setGraph(g));
        return unsub;
    }, []);

    // Re-render every 250ms to animate pulses
    useEffect(() => {
        const t = setInterval(() => setTick((n) => n + 1), 250);
        return () => clearInterval(t);
    }, []);

    // Maintain stable positions for each node id
    const positionFor = useCallback((id) => {
        if (!positionsRef.current.has(id)) {
            // hash-based deterministic placement on concentric rings
            let h = 0;
            for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0;
            const ring = 1 + (Math.abs(h) % 3); // 1..3
            const angle = (Math.abs(h >> 4) % 360) * (Math.PI / 180);
            const radius = 80 + ring * 90 + ((Math.abs(h >> 8) % 40) - 20);
            const px = CENTER.x + Math.cos(angle) * radius;
            const py = CENTER.y + Math.sin(angle) * radius;
            // core_node always at center
            positionsRef.current.set(
                id,
                id === "core_node" ? { x: CENTER.x, y: CENTER.y } : { x: px, y: py },
            );
        }
        return positionsRef.current.get(id);
    }, []);

    const process = async () => {
        if (!input.trim() || busy) return;
        setBusy(true);
        try {
            const result = await runQuantumOS(input.trim());
            setLastResult(result);
            setInput("");
        } catch (_) {/* ignore */}
        finally {
            setBusy(false);
        }
    };

    const reset = () => {
        quantumOS.reset();
        setLastResult(null);
        positionsRef.current.clear();
    };

    const now = Date.now();
    const nodeCount = graph.nodes.length;
    const edgeCount = graph.edges.length;

    return (
        <div className="w-full h-full flex flex-col text-white" data-testid="quantum-screen">
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-3 flex-wrap">
                <Atom size={14} className="text-[#00F0FF] glow" />
                <h3 className="heading text-[11px] uppercase tracking-widest text-[#00F0FF]">
                    quantum mind os // live neural brain
                </h3>
                <span className="label text-[9px] text-[#666]">
                    {nodeCount} nodes · {edgeCount} synapses
                </span>
                <div className="flex-1" />
                <span className="label text-[9px] text-[#666]">
                    updated {graph.updated ? new Date(graph.updated).toLocaleTimeString() : "—"}
                </span>
                <button
                    onClick={reset}
                    data-testid="quantum-reset-btn"
                    className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-[#FF2A2A]/40 text-[#FF2A2A] hover:bg-[#FF2A2A]/10 flex items-center gap-1"
                >
                    <Trash2 size={11} /> wipe
                </button>
            </div>

            <form
                onSubmit={(e) => { e.preventDefault(); process(); }}
                className="px-4 py-3 border-b border-white/10 flex items-center gap-2 bg-[#0A0A0A]"
            >
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="speak to the quantum mind — input collapses across plan / reason / critique layers"
                    className="flex-1 bg-transparent border border-white/15 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#00F0FF]/60"
                    data-testid="quantum-input"
                    disabled={busy}
                />
                <button
                    type="submit"
                    disabled={busy || !input.trim()}
                    data-testid="quantum-process-btn"
                    className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#00F0FF]/60 text-[#00F0FF] hover:bg-[#00F0FF]/10 disabled:opacity-40 flex items-center gap-1"
                >
                    {busy ? <Loader2 size={11} className="animate-spin" /> : <Zap size={11} />}
                    collapse
                </button>
            </form>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 min-h-0">
                {/* SVG Brain */}
                <div
                    className="lg:col-span-3 relative bg-[#020208] overflow-hidden"
                    data-testid="quantum-brain"
                    data-tick={tick}
                >
                    <svg
                        viewBox={`0 0 ${W} ${H}`}
                        preserveAspectRatio="xMidYMid meet"
                        className="absolute inset-0 w-full h-full"
                    >
                        <defs>
                            <radialGradient id="coreGlow">
                                <stop offset="0%" stopColor="#00F0FF" stopOpacity="1" />
                                <stop offset="100%" stopColor="#00F0FF" stopOpacity="0" />
                            </radialGradient>
                            <radialGradient id="nodeFire">
                                <stop offset="0%" stopColor="#FF2A88" stopOpacity="0.9" />
                                <stop offset="100%" stopColor="#FF2A88" stopOpacity="0" />
                            </radialGradient>
                            <pattern id="qgrid" width="40" height="40" patternUnits="userSpaceOnUse">
                                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#00F0FF" strokeWidth="0.4" opacity="0.06" />
                            </pattern>
                        </defs>
                        <rect width={W} height={H} fill="url(#qgrid)" />
                        {/* center origin */}
                        <circle cx={CENTER.x} cy={CENTER.y} r={80} fill="url(#coreGlow)" opacity={0.4} />

                        {/* edges */}
                        {graph.edges.map((e, i) => {
                            const a = positionFor(e.from);
                            const b = positionFor(e.to);
                            const opacity = Math.min(0.15 + (e.weight || 1) * 0.04, 0.7);
                            return (
                                <line
                                    key={`e${i}`}
                                    x1={a.x}
                                    y1={a.y}
                                    x2={b.x}
                                    y2={b.y}
                                    stroke="#00F0FF"
                                    strokeWidth={0.5 + Math.min((e.weight || 1) * 0.3, 2)}
                                    opacity={opacity}
                                />
                            );
                        })}

                        {/* nodes */}
                        {graph.nodes.map((n) => {
                            const p = positionFor(n.id);
                            const age = now - (n.activity || 0);
                            const firing = age < 2000; // recently fired
                            const pulse = firing ? 1 + Math.sin(tick * 0.6) * 0.4 : 1;
                            const r = (3 + (n.size || 1) * 4) * pulse;
                            const isCore = n.id === "core_node";
                            const color = isCore ? "#CCFF00" : firing ? "#FF2A88" : "#00F0FF";
                            return (
                                <g key={n.id} data-testid={`qnode-${n.id.slice(0, 12)}`}>
                                    {firing && (
                                        <circle cx={p.x} cy={p.y} r={r * 2.8} fill="url(#nodeFire)" opacity={0.6} />
                                    )}
                                    <circle
                                        cx={p.x}
                                        cy={p.y}
                                        r={r}
                                        fill={color}
                                        opacity={0.85}
                                        stroke={color}
                                        strokeWidth={firing ? 1.2 : 0.4}
                                    />
                                    <text
                                        x={p.x}
                                        y={p.y - r - 4}
                                        fontSize="9"
                                        fontFamily="ui-monospace, Menlo, monospace"
                                        textAnchor="middle"
                                        fill={isCore ? "#CCFF00" : "rgba(255,255,255,0.7)"}
                                    >
                                        {n.id.length > 22 ? n.id.slice(0, 22) + "…" : n.id}
                                    </text>
                                </g>
                            );
                        })}

                        {/* empty state hint */}
                        {nodeCount === 0 && (
                            <text
                                x={CENTER.x}
                                y={CENTER.y}
                                textAnchor="middle"
                                fontFamily="ui-monospace, Menlo, monospace"
                                fontSize="11"
                                fill="#666"
                            >
                                [VOID] brain dormant. feed input above to seed the lattice.
                            </text>
                        )}
                    </svg>
                </div>

                {/* Sidebar: last collapse result */}
                <div className="overflow-y-auto althea-scroll p-3 border-l border-white/10 bg-[#050505]">
                    <div className="label text-[9px] uppercase text-[#00F0FF] mb-2">
                        last collapse
                    </div>
                    {!lastResult && (
                        <div className="text-[10px] text-[#555]">
                            no collapse yet. enter input above to invoke planner → reasoner → critic and observe the superposition collapse.
                        </div>
                    )}
                    {lastResult && (
                        <div className="space-y-3 text-[10px]" data-testid="quantum-result">
                            <div>
                                <div className="label text-[8px] text-[#666] uppercase mb-1">input</div>
                                <div className="font-mono text-[#CCFF00]">{lastResult.input}</div>
                            </div>
                            <div>
                                <div className="label text-[8px] text-[#666] uppercase mb-1">superposition</div>
                                {lastResult.superposition.map((s, i) => (
                                    <div key={i} className="border-l-2 border-[#00F0FF]/30 pl-2 mb-1 text-white/70 whitespace-pre-wrap">
                                        {s}
                                    </div>
                                ))}
                            </div>
                            <div>
                                <div className="label text-[8px] text-[#FF2A88] uppercase mb-1">collapsed</div>
                                <div className="border-l-2 border-[#FF2A88] pl-2 text-white whitespace-pre-wrap">
                                    {lastResult.collapsed}
                                </div>
                            </div>
                            <div>
                                <div className="label text-[8px] text-[#666] uppercase mb-1">memory</div>
                                <div className="text-white/60 font-mono break-words">
                                    {JSON.stringify(lastResult.memory, null, 2)}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default QuantumScreen;
