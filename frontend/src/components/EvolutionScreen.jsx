import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Atom, Loader2, RotateCw, Zap, Code2 } from "lucide-react";

const ARCHETYPE_COLOR = {
    LINUS: "#FF8800",
    CARMACK: "#00F0FF",
    DIJKSTRA: "#CCFF00",
    HOPPER: "#FF2A88",
    KERNIGHAN: "#A29BFE",
    KAY: "#FFD400",
    THOMPSON: "#00FF99",
    WALL: "#FF6666",
    WOZ: "#FFAA00",
    BACKUS: "#9C88FF",
    SELF: "#CCFF00",
};

const EvolutionScreen = () => {
    const [version, setVersion] = useState(null);
    const [cycles, setCycles] = useState([]);
    const [archetypes, setArchetypes] = useState([]);
    const [busy, setBusy] = useState(false);
    const [selectedArch, setSelectedArch] = useState("");
    const [hint, setHint] = useState("");

    const refresh = useCallback(async () => {
        try {
            const [v, c, a] = await Promise.all([
                axios.get(`${API}/evolution/version`),
                axios.get(`${API}/evolution/cycles?limit=50`),
                axios.get(`${API}/evolution/archetypes`),
            ]);
            setVersion(v.data);
            setCycles(c.data || []);
            setArchetypes(a.data || []);
        } catch (e) {
            console.warn("evolution refresh failed:", e);
        }
    }, []);

    useEffect(() => {
        refresh();
        const t = setInterval(refresh, 10000);
        return () => clearInterval(t);
    }, [refresh]);

    const evolve = async (trigger = "manual") => {
        if (busy) return;
        setBusy(true);
        try {
            await axios.post(`${API}/evolution/tick`, {
                trigger,
                force: true,
                archetype: selectedArch || null,
                intent_hint: hint.trim() || null,
            });
            setHint("");
            await refresh();
        } catch (e) {
            console.warn("evolve failed:", e);
        } finally {
            setBusy(false);
        }
    };

    const masterPull = async (archetype) => {
        if (busy) return;
        setBusy(true);
        try {
            await axios.post(`${API}/evolution/master-update`, { archetype });
            await refresh();
        } catch (e) {/* ignore */}
        finally {
            setBusy(false);
        }
    };

    return (
        <div className="w-full h-full flex flex-col text-white" data-testid="evolution-screen">
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-3 flex-wrap">
                <Atom size={14} className="text-[#FF2A88] glow" />
                <h3 className="heading text-[11px] uppercase tracking-widest text-[#FF2A88]">
                    evolution engine // althea builds herself while idle
                </h3>
                <div className="flex-1" />
                <span className="leading-none">
                    <div className="label text-[9px] uppercase text-[#666]">version</div>
                    <div className="heading text-base text-[#FF2A88] glow" data-testid="evolution-version">
                        v{version?.version || "1.0.0"}
                    </div>
                </span>
                <span className="leading-none">
                    <div className="label text-[9px] uppercase text-[#666]">cycles</div>
                    <div className="heading text-base text-[#CCFF00]" data-testid="evolution-cycle-count">
                        {version?.cycles ?? 0}
                    </div>
                </span>
            </div>

            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2 flex-wrap bg-[#0A0A0A]">
                <select
                    value={selectedArch}
                    onChange={(e) => setSelectedArch(e.target.value)}
                    className="bg-[#080808] border border-white/15 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#FF2A88]/60"
                    data-testid="evolution-archetype-select"
                >
                    <option value="">auto-rotate archetype</option>
                    {archetypes.map((a) => (
                        <option key={a.key} value={a.key}>{a.key}</option>
                    ))}
                </select>
                <input
                    value={hint}
                    onChange={(e) => setHint(e.target.value)}
                    placeholder="intent hint (optional)"
                    className="flex-1 min-w-[200px] bg-transparent border border-white/15 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#FF2A88]/60"
                    data-testid="evolution-hint-input"
                />
                <button
                    onClick={() => evolve("manual")}
                    disabled={busy}
                    data-testid="evolution-tick-btn"
                    className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#FF2A88]/60 text-[#FF2A88] hover:bg-[#FF2A88]/10 disabled:opacity-40 flex items-center gap-1"
                >
                    {busy ? <Loader2 size={11} className="animate-spin" /> : <Zap size={11} />}
                    evolve
                </button>
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 min-h-0">
                {/* Cycle timeline */}
                <div className="lg:col-span-3 overflow-y-auto althea-scroll p-4 space-y-2">
                    {cycles.length === 0 && (
                        <div className="text-[11px] text-[#666] heading uppercase tracking-widest">
                            no cycles yet. autonomous evolution fires every ~75s when idle, or trigger one above.
                        </div>
                    )}
                    {cycles.map((c) => (
                        <CycleCard key={c.id} cycle={c} />
                    ))}
                </div>

                {/* Master archetypes */}
                <div className="overflow-y-auto althea-scroll p-3 border-l border-white/10 bg-[#050505] space-y-2">
                    <div className="label text-[9px] uppercase tracking-widest text-[#FF2A88] mb-2">
                        master-coder channels
                    </div>
                    {archetypes.map((a) => {
                        const color = ARCHETYPE_COLOR[a.key] || "#FF2A88";
                        return (
                            <div
                                key={a.key}
                                className="border p-2 cursor-pointer hover:bg-[#0A0A0A]"
                                style={{ borderColor: color + "30" }}
                                data-testid={`master-${a.key}`}
                                onClick={() => masterPull(a.key)}
                            >
                                <div className="flex items-center justify-between">
                                    <span
                                        className="heading text-[10px] uppercase tracking-widest"
                                        style={{ color }}
                                    >
                                        {a.key}
                                    </span>
                                    <RotateCw size={9} style={{ color }} />
                                </div>
                                <p className="text-[9px] text-[#888] leading-snug mt-1">
                                    {a.doctrine}
                                </p>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

const CycleCard = ({ cycle }) => {
    const color = ARCHETYPE_COLOR[cycle.archetype] || "#FF2A88";
    return (
        <div
            className="border border-white/10 p-3 bg-[#0A0A0A]"
            style={{ borderLeftColor: color, borderLeftWidth: 2 }}
            data-testid={`evolution-cycle-${cycle.cycle_number}`}
        >
            <div className="flex items-center gap-2 flex-wrap">
                <span className="heading text-[12px] uppercase tracking-widest text-white">
                    cycle #{cycle.cycle_number.toString().padStart(4, "0")}
                </span>
                <span
                    className="label text-[9px] uppercase border px-1"
                    style={{ color, borderColor: color + "60" }}
                >
                    {cycle.archetype}
                </span>
                <span className="label text-[9px] text-[#888] font-mono">
                    v{cycle.version_before} → <span style={{ color }}>v{cycle.version_after}</span>
                </span>
                <span className="label text-[9px] uppercase text-[#666]">
                    {cycle.trigger}
                </span>
                {cycle.applied && (
                    <span className="label text-[9px] uppercase border border-[#00F0FF]/40 text-[#00F0FF] px-1">
                        applied
                    </span>
                )}
                <div className="flex-1" />
                <span className="label text-[9px] text-[#666] font-mono">
                    {cycle.node_id}
                </span>
            </div>
            <p className="text-[11px] text-white/85 mt-2 leading-snug">
                {cycle.intent}
            </p>
            <p className="text-[10px] text-[#aaa] mt-1 italic leading-snug">
                <Code2 size={10} className="inline mr-1" />
                {cycle.delta}
            </p>
            <div className="text-[9px] text-[#555] mt-2 font-mono">
                {new Date(cycle.timestamp).toLocaleString()}
            </div>
        </div>
    );
};

export default EvolutionScreen;
