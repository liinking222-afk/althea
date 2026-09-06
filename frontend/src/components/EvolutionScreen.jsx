import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Atom, Loader2, RotateCw, Zap, Play, ShieldCheck, ShieldAlert, Crosshair } from "lucide-react";

const ARCHETYPE_COLOR = {
    LINUS: "#FF8800", CARMACK: "#00F0FF", DIJKSTRA: "#CCFF00", HOPPER: "#FF2A88",
    KERNIGHAN: "#A29BFE", KAY: "#FFD400", THOMPSON: "#00FF99", WALL: "#FF6666",
    WOZ: "#FFAA00", BACKUS: "#9C88FF", SELF: "#CCFF00",
};

const VECTOR_COLOR = {
    PERCEPTION: "#CCFF00", MEMORY: "#FFD400", REASONING: "#00F0FF", SYNTHESIS: "#FF2A88",
    AUTONOMY: "#B347FF", EFFICIENCY: "#48FFB0", CREATIVITY: "#FF9200", RESILIENCE: "#7AF0FF",
};

const EvolutionScreen = () => {
    const [version, setVersion] = useState(null);
    const [cycles, setCycles] = useState([]);
    const [archetypes, setArchetypes] = useState([]);
    const [assessment, setAssessment] = useState(null);
    const [busy, setBusy] = useState(false);
    const [selectedVector, setSelectedVector] = useState("");
    const [selectedArch, setSelectedArch] = useState("");
    const [hint, setHint] = useState("");
    const [lastResult, setLastResult] = useState(null);

    const refresh = useCallback(async () => {
        try {
            const [v, c, a, s] = await Promise.all([
                axios.get(`${API}/evolution/version`),
                axios.get(`${API}/evolution/cycles?limit=40`),
                axios.get(`${API}/evolution/archetypes`),
                axios.get(`${API}/evolution/assessment`),
            ]);
            setVersion(v.data);
            setCycles(c.data || []);
            setArchetypes(a.data || []);
            setAssessment(s.data);
        } catch (e) {
            console.warn("evolution refresh failed:", e);
        }
    }, []);

    useEffect(() => {
        refresh();
        const t = setInterval(refresh, 10000);
        return () => clearInterval(t);
    }, [refresh]);

    const evolve = async (archetype = null) => {
        if (busy) return;
        setBusy(true);
        try {
            const res = await axios.post(`${API}/evolution/tick`, {
                trigger: archetype ? "master" : "manual",
                force: true,
                vector: selectedVector || null,
                archetype: archetype || selectedArch || null,
                intent_hint: hint.trim() || null,
            });
            setLastResult(res.data);
            setHint("");
            await refresh();
        } catch (e) {
            console.warn("evolve failed:", e);
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="w-full h-full flex flex-col text-white" data-testid="evolution-screen">
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-3 flex-wrap">
                <Atom size={14} className="text-[#FF2A88] glow" />
                <h3 className="heading text-[11px] uppercase tracking-widest text-[#FF2A88]">
                    evolution engine {version?.protocol || "AEE/2.0"} // self-directed growth protocol
                </h3>
                <div className="flex-1" />
                <Stat label="version" value={`v${version?.version || "1.0.0"}`} color="#FF2A88" testId="evolution-version" />
                <Stat label="cycles" value={version?.cycles ?? 0} color="#CCFF00" testId="evolution-cycle-count" />
                <Stat label="verified upgrades" value={version?.verified_upgrades ?? 0} color="#48FFB0" testId="evolution-verified-count" />
            </div>

            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2 flex-wrap bg-[#0A0A0A]">
                <select
                    value={selectedVector}
                    onChange={(e) => setSelectedVector(e.target.value)}
                    className="bg-[#080808] border border-white/15 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#FF2A88]/60"
                    data-testid="evolution-vector-select"
                >
                    <option value="">let althea choose (weighted self-assessment)</option>
                    {(version?.vectors || []).map((v) => (
                        <option key={v} value={v}>force {v}</option>
                    ))}
                </select>
                <select
                    value={selectedArch}
                    onChange={(e) => setSelectedArch(e.target.value)}
                    className="bg-[#080808] border border-white/15 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#FF2A88]/60"
                    data-testid="evolution-archetype-select"
                >
                    <option value="">lens: SELF</option>
                    {archetypes.map((a) => (
                        <option key={a.key} value={a.key}>lens: {a.key}</option>
                    ))}
                </select>
                <input
                    value={hint}
                    onChange={(e) => setHint(e.target.value)}
                    placeholder="intent hint (optional — naming a vector forces it)"
                    className="flex-1 min-w-[200px] bg-transparent border border-white/15 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#FF2A88]/60"
                    data-testid="evolution-hint-input"
                />
                <button
                    onClick={() => evolve(null)}
                    disabled={busy}
                    data-testid="evolution-tick-btn"
                    className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#FF2A88]/60 text-[#FF2A88] hover:bg-[#FF2A88]/10 disabled:opacity-40 flex items-center gap-1"
                >
                    {busy ? <Loader2 size={11} className="animate-spin" /> : <Zap size={11} />}
                    self-upgrade
                </button>
            </div>

            {lastResult && <UpgradeBanner result={lastResult} onClose={() => setLastResult(null)} />}

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 min-h-0">
                <div className="lg:col-span-3 overflow-y-auto althea-scroll p-4 space-y-4">
                    <VectorBoard assessment={assessment} />
                    <div className="space-y-2">
                        <div className="label text-[9px] uppercase tracking-widest text-[#888]">
                            upgrade timeline
                        </div>
                        {cycles.length === 0 && (
                            <div className="text-[11px] text-[#666] heading uppercase tracking-widest">
                                no cycles yet. autonomous self-upgrades fire every ~30s while you are around, or trigger one above.
                            </div>
                        )}
                        {cycles.map((c) => <CycleCard key={c.id} cycle={c} />)}
                    </div>
                </div>

                <div className="overflow-y-auto althea-scroll p-3 border-l border-white/10 bg-[#050505] space-y-2">
                    <div className="label text-[9px] uppercase tracking-widest text-[#FF2A88] mb-2">
                        archetype lenses · click to forge through one
                    </div>
                    {archetypes.map((a) => {
                        const color = ARCHETYPE_COLOR[a.key] || "#FF2A88";
                        return (
                            <div
                                key={a.key}
                                className="border p-2 cursor-pointer hover:bg-[#0A0A0A]"
                                style={{ borderColor: color + "30" }}
                                data-testid={`master-${a.key}`}
                                onClick={() => evolve(a.key)}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="heading text-[10px] uppercase tracking-widest" style={{ color }}>
                                        {a.key}
                                    </span>
                                    <RotateCw size={9} style={{ color }} />
                                </div>
                                <p className="text-[9px] text-[#888] leading-snug mt-1">{a.doctrine}</p>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

const Stat = ({ label, value, color, testId }) => (
    <span className="leading-none">
        <div className="label text-[9px] uppercase text-[#666]">{label}</div>
        <div className="heading text-base glow" style={{ color }} data-testid={testId}>{value}</div>
    </span>
);

const UpgradeBanner = ({ result, onClose }) => {
    const color = VECTOR_COLOR[result.target] || "#FF2A88";
    return (
        <div
            className="mx-4 mt-3 border px-3 py-2 text-[11px] font-mono flex items-start gap-3 bg-[#0A0A0A]"
            style={{ borderColor: color + "80" }}
            data-testid="evolution-last-result"
        >
            {result.verified ? <ShieldCheck size={14} style={{ color }} /> : <ShieldAlert size={14} className="text-[#FF6666]" />}
            <div className="flex-1 leading-snug">
                <span style={{ color }}>[SELF-UPGRADE #{result.upgrade_id}]</span>{" "}
                target <b>{result.target}</b> → <b>{result.module}</b> · {result.checks} checks ·{" "}
                v{result.version}
                <div className="text-[#aaa] mt-1">{result.change}</div>
            </div>
            <button onClick={onClose} className="text-[#666] hover:text-white text-[10px]" data-testid="evolution-last-result-close">×</button>
        </div>
    );
};

const VectorBoard = ({ assessment }) => {
    if (!assessment) return null;
    return (
        <div className="border border-white/10 bg-[#0A0A0A] p-3" data-testid="evolution-vector-board">
            <div className="flex items-center gap-2 mb-2">
                <Crosshair size={11} className="text-[#B347FF]" />
                <span className="label text-[9px] uppercase tracking-widest text-[#B347FF]">
                    live self-assessment · what i would upgrade next
                </span>
                <div className="flex-1" />
                <span className="label text-[9px] uppercase text-[#888]">
                    favored: <span style={{ color: VECTOR_COLOR[assessment.favored] }} data-testid="evolution-favored-vector">{assessment.favored}</span>
                </span>
            </div>
            <div className="space-y-1.5">
                {assessment.vectors.map((r) => {
                    const color = VECTOR_COLOR[r.vector] || "#fff";
                    return (
                        <div key={r.vector} className="grid grid-cols-12 items-center gap-2" data-testid={`vector-row-${r.vector}`}>
                            <span className="col-span-2 heading text-[10px] uppercase tracking-widest truncate" style={{ color }}>
                                {r.vector}
                            </span>
                            <div className="col-span-4 h-2 bg-white/5 relative overflow-hidden">
                                <div className="absolute inset-y-0 left-0 transition-[width] duration-700" style={{ width: `${Math.round(r.probability * 100)}%`, background: color }} />
                            </div>
                            <span className="col-span-1 text-[10px] font-mono text-right" style={{ color }}>
                                {Math.round(r.probability * 100)}%
                            </span>
                            <span className="col-span-5 text-[9px] text-[#888] font-mono truncate" title={r.reason}>
                                w{r.base} · pressure {Math.round(r.pressure * 100)}% · {r.upgrades}× · {r.reason}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

const CycleCard = ({ cycle }) => {
    const [running, setRunning] = useState(false);
    const [runOut, setRunOut] = useState(null);
    const color = VECTOR_COLOR[cycle.vector] || ARCHETYPE_COLOR[cycle.archetype] || "#FF2A88";
    const checks = cycle.verification?.checks || [];

    const run = async () => {
        if (running || !cycle.upgrade_id) return;
        setRunning(true);
        try {
            const res = await axios.post(`${API}/evolution/upgrades/${cycle.upgrade_id}/run`, {});
            const r = res.data.result || {};
            const { verification, ...rest } = r;
            setRunOut({ ok: true, ms: res.data.run_ms, passed: verification?.all_passed, body: rest });
        } catch (e) {
            setRunOut({ ok: false, body: e?.response?.data?.detail || String(e) });
        } finally {
            setRunning(false);
        }
    };

    return (
        <div
            className="border border-white/10 p-3 bg-[#0A0A0A]"
            style={{ borderLeftColor: color, borderLeftWidth: 2 }}
            data-testid={`evolution-cycle-${cycle.cycle_number}`}
        >
            <div className="flex items-center gap-2 flex-wrap">
                <span className="heading text-[12px] uppercase tracking-widest text-white">
                    cycle #{String(cycle.cycle_number).padStart(4, "0")}
                </span>
                {cycle.vector && (
                    <span className="label text-[9px] uppercase border px-1" style={{ color, borderColor: color + "60" }}>
                        {cycle.vector}
                    </span>
                )}
                <span className="label text-[9px] uppercase text-[#888]">lens {cycle.archetype}</span>
                <span className="label text-[9px] text-[#888] font-mono">
                    v{cycle.version_before} → <span style={{ color }}>v{cycle.version_after}</span>
                </span>
                <span className="label text-[9px] uppercase text-[#666]">{cycle.trigger}{cycle.forced ? " · forced" : ""}</span>
                {cycle.verified === true && (
                    <span className="label text-[9px] uppercase border border-[#48FFB0]/40 text-[#48FFB0] px-1">verified</span>
                )}
                {cycle.verified === false && (
                    <span className="label text-[9px] uppercase border border-[#FF6666]/40 text-[#FF6666] px-1">unverified</span>
                )}
                <div className="flex-1" />
                {cycle.upgrade_id && <span className="label text-[9px] text-[#666] font-mono">#{cycle.upgrade_id}</span>}
                <span className="label text-[9px] text-[#666] font-mono">{cycle.node_id}</span>
            </div>
            <p className="text-[11px] text-white/85 mt-2 leading-snug">
                {cycle.module ? <span style={{ color }}>{cycle.module}</span> : cycle.intent}
                {cycle.module && <span className="text-[#aaa]"> — {cycle.change || cycle.delta}</span>}
            </p>
            {cycle.assessment_reason && (
                <p className="text-[9px] text-[#777] mt-1 font-mono">why: {cycle.assessment_reason}</p>
            )}
            {checks.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                    {checks.map((c, i) => (
                        <span
                            key={i}
                            className="text-[9px] font-mono px-1 border"
                            style={{ color: c.passed ? "#48FFB0" : "#FF6666", borderColor: (c.passed ? "#48FFB0" : "#FF6666") + "40" }}
                            title={c.query || c.name}
                        >
                            {c.passed ? "✓" : "✗"} {(c.name || c.query || "").slice(0, 44)}
                        </span>
                    ))}
                </div>
            )}
            <div className="flex items-center gap-3 mt-2">
                <span className="text-[9px] text-[#555] font-mono">{new Date(cycle.timestamp).toLocaleString()}</span>
                <div className="flex-1" />
                {cycle.upgrade_id && (
                    <button
                        onClick={run}
                        disabled={running}
                        data-testid={`evolution-run-${cycle.upgrade_id}`}
                        className="text-[9px] heading uppercase tracking-widest px-2 py-0.5 border flex items-center gap-1 hover:bg-white/5 disabled:opacity-40"
                        style={{ color, borderColor: color + "60" }}
                    >
                        {running ? <Loader2 size={9} className="animate-spin" /> : <Play size={9} />}
                        run module
                    </button>
                )}
            </div>
            {runOut && (
                <pre
                    className="mt-2 text-[9px] font-mono text-[#bbb] bg-black/60 border border-white/10 p-2 max-h-40 overflow-auto althea-scroll whitespace-pre-wrap"
                    data-testid={`evolution-run-output-${cycle.upgrade_id}`}
                >
                    {runOut.ok ? `self-test ${runOut.passed ? "PASSED" : "FAILED"} · ${runOut.ms}ms\n` : "error: "}
                    {JSON.stringify(runOut.body, null, 1).slice(0, 1600)}
                </pre>
            )}
        </div>
    );
};

export default EvolutionScreen;
