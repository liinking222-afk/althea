import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import {
    AlertTriangle,
    CheckCircle2,
    Wrench,
    RefreshCw,
    Activity,
    Loader2,
    ShieldAlert,
} from "lucide-react";

const VERDICT_COLOR = {
    ALL_SYSTEMS_NOMINAL: "#CCFF00",
    OK_WITH_NOTES: "#FFD400",
    DEGRADED: "#FF2A88",
};

const TroubleshootScreen = () => {
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(false);
    const [repairing, setRepairing] = useState(false);
    const [repairLog, setRepairLog] = useState([]);

    const run = useCallback(async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API}/diagnostics`);
            setReport(res.data);
        } catch (e) {
            setReport({
                verdict: "DEGRADED",
                severity: "critical",
                checks: [],
                error: e.message,
            });
        } finally {
            setLoading(false);
        }
    }, []);

    const repair = useCallback(async () => {
        setRepairing(true);
        try {
            const res = await axios.post(`${API}/diagnostics/repair`);
            const actions = res.data?.actions || [];
            setRepairLog((log) => [
                {
                    at: new Date().toLocaleTimeString(),
                    actions: actions.length
                        ? actions
                        : ["no repair actions required"],
                },
                ...log,
            ].slice(0, 20));
            // refresh diagnostics after repair
            run();
        } catch (e) {
            setRepairLog((log) => [
                { at: new Date().toLocaleTimeString(), actions: [`error: ${e.message}`] },
                ...log,
            ]);
        } finally {
            setRepairing(false);
        }
    }, [run]);

    useEffect(() => {
        run();
        const t = setInterval(run, 20000);
        return () => clearInterval(t);
    }, [run]);

    const color = VERDICT_COLOR[report?.verdict] || "#666";

    return (
        <div
            className="w-full h-full flex flex-col overflow-y-auto althea-scroll"
            data-testid="troubleshoot-screen"
        >
            <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between gap-2 flex-wrap">
                <div className="flex items-center gap-2">
                    <ShieldAlert size={14} style={{ color }} />
                    <div>
                        <div className="label text-[9px] tracking-widest text-[#888]">
                            self-diagnostics
                        </div>
                        <div
                            className="heading text-sm tracking-widest"
                            style={{ color }}
                            data-testid="troubleshoot-verdict"
                        >
                            {report?.verdict || (loading ? "scanning…" : "—")}
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={run}
                        disabled={loading}
                        data-testid="troubleshoot-rescan"
                        className="heading text-[10px] uppercase tracking-widest px-3 py-1.5 border border-white/15 text-[#888] hover:text-[#CCFF00] hover:border-[#CCFF00]/60 disabled:opacity-40 flex items-center gap-1"
                    >
                        {loading ? (
                            <Loader2 size={11} className="animate-spin" />
                        ) : (
                            <RefreshCw size={11} />
                        )}
                        rescan
                    </button>
                    <button
                        onClick={repair}
                        disabled={repairing}
                        data-testid="troubleshoot-repair"
                        className="heading text-[10px] uppercase tracking-widest px-3 py-1.5 border border-[#FFD400]/60 text-[#FFD400] hover:bg-[#FFD400]/10 disabled:opacity-40 flex items-center gap-1"
                    >
                        {repairing ? (
                            <Loader2 size={11} className="animate-spin" />
                        ) : (
                            <Wrench size={11} />
                        )}
                        repair
                    </button>
                </div>
            </div>

            <div className="px-4 py-3 grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px] border-b border-white/10">
                <Stat
                    label="failures"
                    value={report?.failure_count ?? 0}
                    color={report?.failure_count ? "#FF2A88" : "#666"}
                />
                <Stat
                    label="warnings"
                    value={report?.warning_count ?? 0}
                    color={report?.warning_count ? "#FFD400" : "#666"}
                />
                <Stat
                    label="severity"
                    value={(report?.severity || "—").toUpperCase()}
                    color={color}
                />
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 min-h-0">
                <div className="lg:col-span-2 p-4 space-y-3 overflow-y-auto althea-scroll">
                    <div className="label text-[#888] mb-1">checks</div>
                    {!report?.checks?.length && !loading && (
                        <div className="text-[11px] text-[#555]">
                            no checks reported.
                        </div>
                    )}
                    {(report?.checks || []).map((c) => (
                        <div
                            key={c.name}
                            data-testid={`check-${c.name}`}
                            className={`border-l-2 pl-3 py-2 ${
                                c.ok
                                    ? c.warn
                                        ? "border-[#FFD400] bg-[#FFD400]/5"
                                        : "border-[#CCFF00]/60"
                                    : "border-[#FF2A88] bg-[#FF2A88]/5"
                            }`}
                        >
                            <div className="flex items-center gap-2">
                                {c.ok && !c.warn ? (
                                    <CheckCircle2
                                        size={12}
                                        className="text-[#CCFF00]"
                                    />
                                ) : (
                                    <AlertTriangle
                                        size={12}
                                        className={
                                            c.ok
                                                ? "text-[#FFD400]"
                                                : "text-[#FF2A88]"
                                        }
                                    />
                                )}
                                <span className="heading text-[11px] uppercase tracking-widest text-white">
                                    {c.name}
                                </span>
                                {c.latency_ms !== undefined && (
                                    <span className="label text-[9px] text-[#666]">
                                        · {c.latency_ms}ms
                                    </span>
                                )}
                            </div>
                            {c.error && (
                                <div className="mt-1 text-[10.5px] text-[#FF2A88] font-mono">
                                    error: {c.error}
                                </div>
                            )}
                            {c.warn && (
                                <div className="mt-1 text-[10.5px] text-[#FFD400]">
                                    warning: {c.warn}
                                </div>
                            )}
                            {c.remedy && (
                                <div className="mt-1 text-[10.5px] text-white/70">
                                    fix: {c.remedy}
                                </div>
                            )}
                            {/* show extra metrics inline */}
                            <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5">
                                {Object.entries(c)
                                    .filter(
                                        ([k]) =>
                                            ![
                                                "name",
                                                "ok",
                                                "remedy",
                                                "error",
                                                "warn",
                                                "latency_ms",
                                            ].includes(k),
                                    )
                                    .slice(0, 6)
                                    .map(([k, v]) => (
                                        <span
                                            key={k}
                                            className="text-[10px] text-[#666]"
                                        >
                                            {k}=
                                            <span className="text-white/70">
                                                {Array.isArray(v)
                                                    ? `[${v.length}]`
                                                    : typeof v === "object"
                                                      ? JSON.stringify(v).slice(0, 40)
                                                      : String(v).slice(0, 40)}
                                            </span>
                                        </span>
                                    ))}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="border-l border-white/10 p-3 overflow-y-auto althea-scroll bg-[#050505]">
                    <div className="label text-[#888] mb-2 flex items-center gap-1">
                        <Activity size={10} /> repair log
                    </div>
                    {!repairLog.length && (
                        <div className="text-[10px] text-[#555]">
                            no repair actions yet. press REPAIR above.
                        </div>
                    )}
                    {repairLog.map((entry, i) => (
                        <div
                            key={`${entry.at}-${i}`}
                            className="text-[10px] mb-2 border-l-2 border-[#FFD400]/40 pl-2"
                        >
                            <div className="text-[#FFD400] tracking-widest">
                                {entry.at}
                            </div>
                            {entry.actions.map((a, j) => (
                                <div key={j} className="text-white/80">
                                    · {a}
                                </div>
                            ))}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

const Stat = ({ label, value, color }) => (
    <div className="border border-white/10 px-3 py-2">
        <div className="label text-[9px] text-[#666]">{label}</div>
        <div
            className="heading text-base tracking-widest"
            style={{ color }}
            data-testid={`troubleshoot-stat-${label}`}
        >
            {value}
        </div>
    </div>
);

export default TroubleshootScreen;
