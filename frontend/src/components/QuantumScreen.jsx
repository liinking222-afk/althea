import React, { useEffect, useRef, useState, useCallback } from "react";
import { quantumOS, runQuantumOS } from "@/lib/quantumMindOS";
import { Atom, Loader2, Trash2, Zap, Activity, Flame, Network, ScrollText, Maximize2, X } from "lucide-react";

const W = 1000;
const H = 600;
const CENTER = { x: W / 2, y: H / 2 };

const QuantumScreen = () => {
    const [graph, setGraph] = useState(quantumOS.snapshot());
    const [input, setInput] = useState("");
    const [busy, setBusy] = useState(false);
    const [lastResult, setLastResult] = useState(null);
    const [tick, setTick] = useState(0);
    const [log, setLog] = useState([]);
    const [pulseHistory, setPulseHistory] = useState([]);
    const [maximized, setMaximized] = useState(null); // 'pulse'|'top'|'synapse'|'log'|null
    const positionsRef = useRef(new Map());

    useEffect(() => {
        const unsub = quantumOS.subscribe((g) => {
            setGraph(g);
            // sample firing count for pulse history
            const fired = g.nodes.filter((n) => Date.now() - (n.activity || 0) < 2500).length;
            setPulseHistory((h) => [...h.slice(-59), fired]);
        });
        return unsub;
    }, []);

    // 250ms pulse ticker
    useEffect(() => {
        const t = setInterval(() => setTick((n) => n + 1), 250);
        return () => clearInterval(t);
    }, []);

    // Sample pulse every second even without new collapses
    useEffect(() => {
        const t = setInterval(() => {
            const fired = graph.nodes.filter((n) => Date.now() - (n.activity || 0) < 2500).length;
            setPulseHistory((h) => [...h.slice(-59), fired]);
        }, 1000);
        return () => clearInterval(t);
    }, [graph]);

    const positionFor = useCallback((id) => {
        if (!positionsRef.current.has(id)) {
            let h = 0;
            for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0;
            const ring = 1 + (Math.abs(h) % 3);
            const angle = (Math.abs(h >> 4) % 360) * (Math.PI / 180);
            const radius = 80 + ring * 90 + ((Math.abs(h >> 8) % 40) - 20);
            const px = CENTER.x + Math.cos(angle) * radius;
            const py = CENTER.y + Math.sin(angle) * radius;
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
            setLog((l) => [
                {
                    id: crypto.randomUUID(),
                    at: Date.now(),
                    input: input.trim(),
                    collapsed: typeof result === "string" ? result : result.collapsed,
                    nodes: typeof result === "string" ? 0 : result.brain.nodes.length,
                },
                ...l.slice(0, 99),
            ]);
            setInput("");
        } catch (_) {/* ignore */}
        finally {
            setBusy(false);
        }
    };

    const reset = () => {
        quantumOS.reset();
        setLastResult(null);
        setLog([]);
        setPulseHistory([]);
        positionsRef.current.clear();
    };

    const now = Date.now();
    const nodeCount = graph.nodes.length;
    const edgeCount = graph.edges.length;
    const firingCount = graph.nodes.filter((n) => now - (n.activity || 0) < 2500).length;

    return (
        <div className="w-full h-full flex flex-col text-white" data-testid="quantum-screen">
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-3 flex-wrap">
                <Atom size={14} className="text-[#00F0FF] glow" />
                <h3 className="heading text-[11px] uppercase tracking-widest text-[#00F0FF]">
                    quantum mind os // live neural brain
                </h3>
                <span className="label text-[9px] text-[#666]">
                    {nodeCount} nodes · {edgeCount} synapses · {firingCount} firing
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
                {/* Main SVG Brain */}
                <div
                    className="lg:col-span-3 relative bg-[#020208] overflow-hidden flex flex-col"
                    data-tick={tick}
                >
                    <div className="flex-1 relative" data-testid="quantum-brain">
                        <BrainSvg
                            graph={graph}
                            positionFor={positionFor}
                            tick={tick}
                            now={now}
                            nodeCount={nodeCount}
                        />
                    </div>
                    {/* Bottom row of secondary displays */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 border-t border-white/10 min-h-[160px] bg-[#050505]">
                        <PulseMeter history={pulseHistory} onExpand={() => setMaximized("pulse")} />
                        <TopNeurons nodes={graph.nodes} onExpand={() => setMaximized("top")} />
                        <SynapseHeat edges={graph.edges} onExpand={() => setMaximized("synapse")} />
                        <ActivityLog log={log} onExpand={() => setMaximized("log")} />
                    </div>
                </div>

                {/* Last collapse sidebar */}
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

            {/* Fullscreen modal for any panel */}
            {maximized && (
                <MaximizedPanel
                    which={maximized}
                    onClose={() => setMaximized(null)}
                    pulseHistory={pulseHistory}
                    nodes={graph.nodes}
                    edges={graph.edges}
                    log={log}
                />
            )}
        </div>
    );
};

// ─── Sub-components ───────────────────────────────────────────────

const BrainSvg = ({ graph, positionFor, tick, now, nodeCount }) => (
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
        <circle cx={CENTER.x} cy={CENTER.y} r={80} fill="url(#coreGlow)" opacity={0.4} />
        {graph.edges.map((e, i) => {
            const a = positionFor(e.from);
            const b = positionFor(e.to);
            const opacity = Math.min(0.15 + (e.weight || 1) * 0.04, 0.7);
            return (
                <line key={`e${i}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                    stroke="#00F0FF"
                    strokeWidth={0.5 + Math.min((e.weight || 1) * 0.3, 2)}
                    opacity={opacity}
                />
            );
        })}
        {graph.nodes.map((n) => {
            const p = positionFor(n.id);
            const age = now - (n.activity || 0);
            const firing = age < 2000;
            const pulse = firing ? 1 + Math.sin(tick * 0.6) * 0.4 : 1;
            const r = (3 + (n.size || 1) * 4) * pulse;
            const isCore = n.id === "core_node";
            const color = isCore ? "#CCFF00" : firing ? "#FF2A88" : "#00F0FF";
            return (
                <g key={n.id} data-testid={`qnode-${n.id.slice(0, 12)}`}>
                    {firing && (
                        <circle cx={p.x} cy={p.y} r={r * 2.8} fill="url(#nodeFire)" opacity={0.6} />
                    )}
                    <circle cx={p.x} cy={p.y} r={r} fill={color} opacity={0.85} stroke={color} strokeWidth={firing ? 1.2 : 0.4} />
                    <text x={p.x} y={p.y - r - 4} fontSize="9" fontFamily="ui-monospace, Menlo, monospace" textAnchor="middle" fill={isCore ? "#CCFF00" : "rgba(255,255,255,0.7)"}>
                        {n.id.length > 22 ? n.id.slice(0, 22) + "…" : n.id}
                    </text>
                </g>
            );
        })}
        {nodeCount === 0 && (
            <text x={CENTER.x} y={CENTER.y} textAnchor="middle" fontFamily="ui-monospace, Menlo, monospace" fontSize="11" fill="#666">
                [VOID] brain dormant. feed input above to seed the lattice.
            </text>
        )}
    </svg>
);

// ─── Pulse Meter ──────────────────────────────────────────────────
const PulseMeter = ({ history, onExpand, large }) => {
    const max = Math.max(1, ...history);
    const bars = history.slice(-(large ? 120 : 40));
    return (
        <PanelShell title="pulse meter" testid="qpanel-pulse" icon={Activity} color="#FF2A88" onExpand={onExpand} large={large}>
            <div className="flex items-end gap-0.5 h-full w-full px-2 pb-2">
                {bars.map((v, i) => (
                    <div
                        key={i}
                        className="flex-1 bg-[#FF2A88] transition-all"
                        style={{
                            height: `${(v / max) * 100}%`,
                            minHeight: 1,
                            opacity: 0.35 + (i / bars.length) * 0.65,
                            boxShadow: i >= bars.length - 3 ? "0 0 6px #FF2A88" : "none",
                        }}
                    />
                ))}
                {bars.length === 0 && (
                    <span className="text-[#555] text-[10px]">no pulse data</span>
                )}
            </div>
        </PanelShell>
    );
};

// ─── Top Neurons ──────────────────────────────────────────────────
const TopNeurons = ({ nodes, onExpand, large }) => {
    const top = [...nodes]
        .filter((n) => n.id !== "core_node")
        .sort((a, b) => (b.strength || 0) - (a.strength || 0))
        .slice(0, large ? 30 : 6);
    const max = Math.max(1, ...top.map((n) => n.strength || 0));
    return (
        <PanelShell title="top neurons" testid="qpanel-top" icon={Flame} color="#FFD400" onExpand={onExpand} large={large}>
            <div className="px-2 pb-2 space-y-1 overflow-y-auto althea-scroll h-full">
                {top.length === 0 && (
                    <div className="text-[#555] text-[10px]">no neurons fired yet.</div>
                )}
                {top.map((n) => (
                    <div key={n.id} className="flex items-center gap-2 text-[9px]">
                        <span className="text-white/80 truncate w-24 font-mono">
                            {n.id.slice(0, 18)}
                        </span>
                        <div className="flex-1 bg-white/5 h-1.5 relative">
                            <div
                                className="absolute inset-y-0 left-0 bg-[#FFD400]"
                                style={{ width: `${((n.strength || 0) / max) * 100}%` }}
                            />
                        </div>
                        <span className="text-[#FFD400] font-mono w-10 text-right">
                            {(n.strength || 0).toFixed(2)}
                        </span>
                    </div>
                ))}
            </div>
        </PanelShell>
    );
};

// ─── Synapse Heat ─────────────────────────────────────────────────
const SynapseHeat = ({ edges, onExpand, large }) => {
    // Deduplicate undirected edges
    const seen = new Set();
    const unique = [];
    for (const e of edges) {
        const key = [e.from, e.to].sort().join("|");
        if (seen.has(key)) continue;
        seen.add(key);
        unique.push(e);
    }
    const top = unique.sort((a, b) => (b.weight || 0) - (a.weight || 0)).slice(0, large ? 30 : 5);
    return (
        <PanelShell title="synapse heat" testid="qpanel-synapse" icon={Network} color="#00F0FF" onExpand={onExpand} large={large}>
            <div className="px-2 pb-2 space-y-1 overflow-y-auto althea-scroll h-full">
                {top.length === 0 && (
                    <div className="text-[#555] text-[10px]">no synapses formed.</div>
                )}
                {top.map((e, i) => (
                    <div key={i} className="text-[9px] flex items-center gap-2">
                        <span
                            className="w-1.5 h-1.5 rounded-full"
                            style={{
                                background: "#00F0FF",
                                boxShadow: `0 0 ${Math.min((e.weight || 0) * 4, 12)}px #00F0FF`,
                            }}
                        />
                        <span className="text-white/80 truncate flex-1 font-mono">
                            {e.from.slice(0, 12)} ↔ {e.to.slice(0, 12)}
                        </span>
                        <span className="text-[#00F0FF] font-mono">
                            {(e.weight || 0).toFixed(2)}
                        </span>
                    </div>
                ))}
            </div>
        </PanelShell>
    );
};

// ─── Activity Log ─────────────────────────────────────────────────
const ActivityLog = ({ log, onExpand, large }) => (
    <PanelShell title="activity log" testid="qpanel-log" icon={ScrollText} color="#CCFF00" onExpand={onExpand} large={large}>
        <div className="px-2 pb-2 space-y-1 overflow-y-auto althea-scroll h-full">
            {log.length === 0 && (
                <div className="text-[#555] text-[10px]">no collapse events yet.</div>
            )}
            {log.slice(0, large ? 100 : 8).map((e) => (
                <div key={e.id} className="text-[9px] border-l border-[#CCFF00]/30 pl-2 leading-snug">
                    <div className="text-[#666] font-mono">
                        {new Date(e.at).toLocaleTimeString()}
                    </div>
                    <div className="text-[#CCFF00] truncate">› {e.input}</div>
                    <div className="text-white/60 truncate">{e.collapsed}</div>
                </div>
            ))}
        </div>
    </PanelShell>
);

// ─── Shared shell for sub-windows ─────────────────────────────────
const PanelShell = ({ title, testid, icon: Icon, color, onExpand, large, children }) => (
    <div
        className={`flex flex-col border-r border-white/10 last:border-r-0 ${large ? "h-full" : "h-[160px]"}`}
        data-testid={testid}
    >
        <div className="flex items-center justify-between px-2 py-1 border-b border-white/5 bg-[#080808]">
            <div className="flex items-center gap-1.5">
                <Icon size={9} style={{ color }} />
                <span
                    className="heading text-[9px] uppercase tracking-widest"
                    style={{ color }}
                >
                    {title}
                </span>
            </div>
            {onExpand && !large && (
                <button
                    onClick={onExpand}
                    data-testid={`${testid}-expand`}
                    className="text-[#666] hover:text-white"
                    title="expand"
                >
                    <Maximize2 size={9} />
                </button>
            )}
        </div>
        <div className="flex-1 min-h-0">{children}</div>
    </div>
);

// ─── Fullscreen modal ─────────────────────────────────────────────
const MaximizedPanel = ({ which, onClose, pulseHistory, nodes, edges, log }) => {
    const titleMap = {
        pulse: "pulse meter",
        top: "top neurons",
        synapse: "synapse heat",
        log: "activity log",
    };
    return (
        <div
            className="absolute inset-0 z-50 bg-[#050505]/95 backdrop-blur-sm flex flex-col"
            data-testid="quantum-maximized"
        >
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                <h3 className="heading text-[11px] uppercase tracking-widest text-[#00F0FF]">
                    {titleMap[which]} // expanded
                </h3>
                <button
                    onClick={onClose}
                    data-testid="quantum-maximized-close"
                    className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-white/15 hover:border-white text-white/70 hover:text-white flex items-center gap-1"
                >
                    <X size={11} /> close
                </button>
            </div>
            <div className="flex-1 min-h-0">
                {which === "pulse" && <PulseMeter history={pulseHistory} large />}
                {which === "top" && <TopNeurons nodes={nodes} large />}
                {which === "synapse" && <SynapseHeat edges={edges} large />}
                {which === "log" && <ActivityLog log={log} large />}
            </div>
        </div>
    );
};

export default QuantumScreen;
