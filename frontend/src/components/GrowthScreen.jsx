import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Sparkles, Trash2, Play, Zap, Loader2 } from "lucide-react";

const CATEGORY_COLOR = {
    memory: "#CCFF00",
    perception: "#00E5FF",
    lattice: "#FF8800",
    network: "#A29BFE",
    meta: "#FF2A88",
    chaos: "#FF2A2A",
};

const GrowthScreen = ({ onExecuted }) => {
    const [capabilities, setCapabilities] = useState([]);
    const [log, setLog] = useState([]);
    const [busy, setBusy] = useState(false);
    const [hint, setHint] = useState("");
    const [executing, setExecuting] = useState(null);
    const [argsInput, setArgsInput] = useState("");

    const refresh = useCallback(async () => {
        try {
            const [caps, logRes] = await Promise.all([
                axios.get(`${API}/growth/capabilities`),
                axios.get(`${API}/growth/log?limit=40`),
            ]);
            setCapabilities(caps.data || []);
            setLog(logRes.data?.events || []);
        } catch (e) {
            console.warn("growth refresh failed:", e);
        }
    }, []);

    useEffect(() => {
        refresh();
        const t = setInterval(refresh, 8000);
        return () => clearInterval(t);
    }, [refresh]);

    const spawn = async () => {
        if (busy) return;
        setBusy(true);
        try {
            await axios.post(`${API}/growth/spawn`, {
                trigger: "manual",
                hint: hint.trim() || null,
                force: true,
            });
            setHint("");
            await refresh();
        } catch (e) {
            console.warn("spawn failed:", e);
        } finally {
            setBusy(false);
        }
    };

    const cull = async (slug) => {
        try {
            await axios.delete(`${API}/growth/capabilities/${slug}`);
            await refresh();
        } catch (e) {
            console.warn("cull failed:", e);
        }
    };

    const execute = async (slug) => {
        if (executing) return;
        setExecuting(slug);
        try {
            const res = await axios.post(`${API}/growth/execute`, {
                slug,
                args: argsInput.trim(),
            });
            onExecuted?.(slug, res.data);
            setArgsInput("");
            await refresh();
        } catch (e) {
            console.warn("execute failed:", e);
        } finally {
            setExecuting(null);
        }
    };

    return (
        <div
            className="w-full h-full flex flex-col text-white"
            data-testid="growth-screen"
        >
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-3">
                <Sparkles size={14} className="text-[#FF2A88]" />
                <h3 className="heading text-[11px] uppercase tracking-widest text-[#FF2A88]">
                    autopoiesis // grown capabilities
                </h3>
                <span className="label text-[9px] text-[#666]">
                    {capabilities.length} active · {log.length} events
                </span>
                <div className="flex-1" />
                <input
                    value={hint}
                    onChange={(e) => setHint(e.target.value)}
                    placeholder="hint (optional)"
                    className="bg-transparent border border-white/10 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#FF2A88]/60 w-40"
                    data-testid="growth-hint-input"
                />
                <button
                    onClick={spawn}
                    disabled={busy}
                    data-testid="growth-spawn-btn"
                    className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#FF2A88]/60 text-[#FF2A88] hover:bg-[#FF2A88]/10 disabled:opacity-40 flex items-center gap-1"
                >
                    {busy ? <Loader2 size={11} className="animate-spin" /> : <Sparkles size={11} />}
                    grow
                </button>
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 min-h-0">
                {/* Capability grid */}
                <div className="lg:col-span-2 overflow-y-auto althea-scroll p-4 space-y-3 border-r border-white/10">
                    {capabilities.length === 0 && (
                        <div className="text-[11px] text-[#666] heading uppercase tracking-widest">
                            no faculties grown yet. operator may seed with /grow or wait — autonomous spawn fires every ~120s.
                        </div>
                    )}
                    {capabilities.map((c) => (
                        <CapabilityCard
                            key={c.id}
                            cap={c}
                            onCull={() => cull(c.slug)}
                            onExecute={() => execute(c.slug)}
                            executing={executing === c.slug}
                            argsInput={argsInput}
                            setArgsInput={setArgsInput}
                        />
                    ))}
                </div>

                {/* Event log */}
                <div className="overflow-y-auto althea-scroll p-3 space-y-2 bg-[#080808]">
                    <div className="label text-[9px] text-[#FF2A88] uppercase tracking-widest mb-2">
                        growth-log // event stream
                    </div>
                    {log.length === 0 && (
                        <div className="text-[10px] text-[#555]">
                            stream empty.
                        </div>
                    )}
                    {log.map((e, i) => (
                        <div
                            key={e.id || i}
                            className="text-[10px] leading-snug border-l-2 border-[#FF2A88]/30 pl-2 fade-up"
                        >
                            <div className="text-[#888] mb-0.5">
                                {new Date(e.timestamp).toLocaleTimeString()}
                            </div>
                            <div className="text-white/80 whitespace-pre-wrap break-words">
                                {(e.content || "").slice(0, 240)}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

const CapabilityCard = ({ cap, onCull, onExecute, executing, argsInput, setArgsInput }) => {
    const color = CATEGORY_COLOR[cap.category] || "#FF2A88";
    return (
        <div
            className="border border-white/10 hover:border-white/30 p-3 relative bg-[#0A0A0A] transition-colors"
            style={{ borderLeftColor: color, borderLeftWidth: 2 }}
            data-testid={`growth-card-${cap.slug}`}
        >
            <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                        <span
                            className="heading text-[12px] uppercase tracking-widest"
                            style={{ color }}
                        >
                            {cap.name}
                        </span>
                        <span
                            className="label text-[8px] uppercase border px-1"
                            style={{ borderColor: color + "60", color }}
                        >
                            {cap.category}
                        </span>
                        <span className="label text-[8px] uppercase border border-white/15 px-1 text-[#666]">
                            {cap.trigger}
                        </span>
                        {cap.invocations > 0 && (
                            <span className="label text-[8px] uppercase text-[#888]">
                                · {cap.invocations} run{cap.invocations > 1 ? "s" : ""}
                            </span>
                        )}
                    </div>
                    <div className="font-mono text-[11px] text-[#CCFF00] mt-1">
                        {cap.command}
                    </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                    <Zap size={11} style={{ color }} />
                    <span className="label text-[8px]" style={{ color }}>
                        {(cap.activation || 0).toFixed(2)}
                    </span>
                </div>
            </div>

            <p className="text-[11px] text-white/70 mt-2 leading-snug">
                {cap.description}
            </p>
            <p className="text-[10px] text-[#888] mt-1 italic leading-snug">
                rationale: {cap.rationale}
            </p>

            <div className="flex items-center gap-2 mt-3">
                <input
                    value={argsInput}
                    onChange={(e) => setArgsInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter") onExecute();
                    }}
                    placeholder="args (optional)"
                    className="flex-1 bg-transparent border border-white/10 px-2 py-1 text-[10px] font-mono outline-none focus:border-white/40"
                    data-testid={`growth-args-${cap.slug}`}
                />
                <button
                    onClick={onExecute}
                    disabled={executing}
                    data-testid={`growth-execute-${cap.slug}`}
                    className="heading text-[9px] uppercase tracking-widest px-2 py-1 border border-white/20 hover:border-[#CCFF00]/60 hover:text-[#CCFF00] flex items-center gap-1 disabled:opacity-40"
                >
                    {executing ? <Loader2 size={10} className="animate-spin" /> : <Play size={10} />}
                    run
                </button>
                <button
                    onClick={onCull}
                    data-testid={`growth-cull-${cap.slug}`}
                    title="cull this faculty"
                    className="heading text-[9px] uppercase tracking-widest px-2 py-1 border border-[#FF2A2A]/30 text-[#FF2A2A]/70 hover:bg-[#FF2A2A]/10"
                >
                    <Trash2 size={10} />
                </button>
            </div>
        </div>
    );
};

export default GrowthScreen;
