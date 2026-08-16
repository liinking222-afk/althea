import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Cpu, Zap, Power, Loader2 } from "lucide-react";

const WorkerCoresPanel = () => {
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(null);

    const load = useCallback(async () => {
        try {
            const res = await axios.get(`${API}/workers`);
            setData(res.data);
        } catch (e) {
            console.warn("worker poll failed", e);
        }
    }, []);

    useEffect(() => {
        load();
        const t = setInterval(load, 3000);
        return () => clearInterval(t);
    }, [load]);

    const kick = async (id) => {
        setBusy(id);
        try {
            await axios.post(`${API}/workers/${id}/kick`);
            await load();
        } finally {
            setBusy(null);
        }
    };
    const toggle = async (id) => {
        try {
            await axios.post(`${API}/workers/${id}/toggle`);
            await load();
        } catch (e) {
            console.warn("toggle failed", e);
        }
    };
    const dispatchAll = async () => {
        setBusy("all");
        try {
            await axios.post(`${API}/workers/dispatch`);
            await load();
        } finally {
            setBusy(null);
        }
    };

    return (
        <div
            className="border border-white/10 p-3 bg-black/50"
            data-testid="worker-cores-panel"
        >
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <Cpu size={12} className="text-[#FF2A88]" />
                    <div className="heading text-[10px] uppercase tracking-widest text-white">
                        8-core mesh
                    </div>
                    {data?.loop_running ? (
                        <span
                            className="label text-[9px] px-1 border border-[#CCFF00]/60 text-[#CCFF00]"
                            title="worker loop running"
                        >
                            live
                        </span>
                    ) : (
                        <span className="label text-[9px] px-1 border border-[#666]/60 text-[#666]">
                            stopped
                        </span>
                    )}
                </div>
                <button
                    onClick={dispatchAll}
                    disabled={busy === "all"}
                    data-testid="worker-dispatch-all"
                    title="fire every core once, in parallel"
                    className="heading text-[9px] uppercase tracking-widest px-2 py-0.5 border border-[#FF2A88]/40 text-[#FF2A88] hover:bg-[#FF2A88]/10 disabled:opacity-40 flex items-center gap-1"
                >
                    {busy === "all" ? (
                        <Loader2 size={9} className="animate-spin" />
                    ) : (
                        <Zap size={9} />
                    )}
                    sweep
                </button>
            </div>
            <div className="text-[9px] text-[#666] mb-2 flex justify-between">
                <span>
                    jobs done · <span className="text-white/80">{data?.total_jobs ?? 0}</span>
                </span>
                <span>
                    sweep cycle · <span className="text-white/80">{data?.sweep_seconds ?? 0}s</span>
                </span>
            </div>
            <div className="grid grid-cols-2 gap-1.5">
                {(data?.cores || []).map((c) => {
                    const ageMs = c.last_at
                        ? Date.now() - new Date(c.last_at).getTime()
                        : Infinity;
                    const fresh = ageMs < 20000;
                    return (
                        <div
                            key={c.id}
                            className="border border-white/10 p-1.5 relative"
                            data-testid={`worker-core-${c.id}`}
                            style={{
                                boxShadow: fresh
                                    ? `inset 2px 0 0 0 ${c.color}`
                                    : "inset 2px 0 0 0 #333",
                            }}
                        >
                            <div className="flex items-center justify-between mb-0.5">
                                <div
                                    className="label text-[8px] tracking-widest"
                                    style={{ color: c.color }}
                                >
                                    {c.name.replace("-CORE", "")}
                                </div>
                                <div className="flex items-center gap-0.5">
                                    <button
                                        onClick={() => kick(c.id)}
                                        disabled={busy === c.id}
                                        data-testid={`worker-kick-${c.id}`}
                                        title="tick this core now"
                                        className="text-[#888] hover:text-[#CCFF00] disabled:opacity-30 p-0.5"
                                    >
                                        {busy === c.id ? (
                                            <Loader2 size={8} className="animate-spin" />
                                        ) : (
                                            <Zap size={8} />
                                        )}
                                    </button>
                                    <button
                                        onClick={() => toggle(c.id)}
                                        title={c.active ? "disable" : "enable"}
                                        data-testid={`worker-toggle-${c.id}`}
                                        className={`p-0.5 ${
                                            c.active
                                                ? "text-[#CCFF00]"
                                                : "text-[#666] hover:text-[#FF2A88]"
                                        }`}
                                    >
                                        <Power size={8} />
                                    </button>
                                </div>
                            </div>
                            <div
                                className="text-[9px] text-white/70 truncate leading-tight"
                                title={c.last_task}
                            >
                                {c.last_task || "idle"}
                            </div>
                            <div className="flex items-center justify-between text-[8px] text-[#555] mt-0.5">
                                <span>{c.specialty}</span>
                                <span>
                                    {c.jobs_done}j · {(c.avg_ms || 0).toFixed(0)}ms
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default WorkerCoresPanel;
