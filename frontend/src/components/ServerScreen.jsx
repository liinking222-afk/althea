import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Server, Loader2, Trash2, Activity, ShieldAlert } from "lucide-react";

const PROTOCOLS = ["https", "http", "ssh", "ftp", "redis", "postgres", "mongo", "mysql"];

const STATUS_COLOR = {
    REACHABLE: "#CCFF00",
    UNREACHABLE: "#FF2A2A",
    GATED: "#FF8800",
    STANDBY: "#888",
};

const ServerScreen = () => {
    const [host, setHost] = useState("");
    const [protocol, setProtocol] = useState("https");
    const [port, setPort] = useState("");
    const [busy, setBusy] = useState(false);
    const [list, setList] = useState([]);
    const [lastResult, setLastResult] = useState(null);

    const refresh = useCallback(async () => {
        try {
            const res = await axios.get(`${API}/server/connections`);
            setList(res.data || []);
        } catch (_) {/* ignore */}
    }, []);

    useEffect(() => {
        refresh();
        const t = setInterval(refresh, 10000);
        return () => clearInterval(t);
    }, [refresh]);

    const diagnose = async (e) => {
        e?.preventDefault?.();
        if (!host.trim() || busy) return;
        setBusy(true);
        try {
            const body = { host: host.trim(), protocol };
            if (port.trim()) body.port = parseInt(port.trim(), 10);
            const res = await axios.post(`${API}/server/diagnose`, body);
            setLastResult(res.data);
            await refresh();
        } catch (e) {
            setLastResult({ host: host.trim(), status: "UNREACHABLE", details: { error: e.message } });
        } finally {
            setBusy(false);
        }
    };

    const removeOne = async (id) => {
        await axios.delete(`${API}/server/connections/${id}`);
        refresh();
    };
    const clearAll = async () => {
        await axios.delete(`${API}/server/connections`);
        refresh();
    };

    return (
        <div className="w-full h-full flex flex-col text-white" data-testid="server-screen">
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2 flex-wrap">
                <Server size={13} className="text-[#FF8800]" />
                <h3 className="heading text-[11px] uppercase tracking-widest text-[#FF8800]">
                    server bridge // diagnose · probe · gated-connect
                </h3>
                <span className="label text-[9px] text-[#666]">{list.length} known</span>
                <div className="flex-1" />
                <button
                    onClick={clearAll}
                    data-testid="server-clear"
                    className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-[#FF2A2A]/40 text-[#FF2A2A] hover:bg-[#FF2A2A]/10 flex items-center gap-1"
                >
                    <Trash2 size={10} /> purge
                </button>
            </div>

            <form onSubmit={diagnose} className="px-4 py-3 border-b border-white/10 flex items-center gap-2 flex-wrap bg-[#0A0A0A]">
                <input
                    value={host}
                    onChange={(e) => setHost(e.target.value)}
                    placeholder="host — e.g. example.com or 1.1.1.1"
                    className="flex-1 min-w-[180px] bg-transparent border border-white/15 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#FF8800]/60"
                    data-testid="server-host-input"
                />
                <select
                    value={protocol}
                    onChange={(e) => setProtocol(e.target.value)}
                    className="bg-[#080808] border border-white/15 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#FF8800]/60"
                    data-testid="server-protocol-select"
                >
                    {PROTOCOLS.map((p) => (
                        <option key={p} value={p}>{p.toUpperCase()}</option>
                    ))}
                </select>
                <input
                    value={port}
                    onChange={(e) => setPort(e.target.value)}
                    placeholder="port"
                    className="w-20 bg-transparent border border-white/15 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#FF8800]/60"
                    data-testid="server-port-input"
                />
                <button
                    type="submit"
                    disabled={busy || !host.trim()}
                    data-testid="server-diagnose-btn"
                    className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#FF8800]/60 text-[#FF8800] hover:bg-[#FF8800]/10 disabled:opacity-40 flex items-center gap-1"
                >
                    {busy ? <Loader2 size={11} className="animate-spin" /> : <Activity size={11} />}
                    diagnose
                </button>
            </form>

            <div className="flex-1 overflow-y-auto althea-scroll p-4 space-y-3 bg-[#080808]">
                {lastResult && <ServerCard result={lastResult} highlight />}
                {list.length === 0 && !lastResult && (
                    <div className="text-[#666] text-[11px] heading uppercase tracking-widest">
                        no servers probed. enter a host to begin diagnosis.
                    </div>
                )}
                {list.map((s) => (
                    <ServerCard key={s.id} result={s} onRemove={() => removeOne(s.id)} />
                ))}
            </div>
        </div>
    );
};

const ServerCard = ({ result, highlight, onRemove }) => {
    const color = STATUS_COLOR[result.status] || "#888";
    const d = result.details || {};
    return (
        <div
            className={`border p-3 ${highlight ? "border-white/30 bg-[#0d0d0d]" : "border-white/10"}`}
            style={{ borderLeftColor: color, borderLeftWidth: 2 }}
            data-testid={`server-card-${result.host}`}
        >
            <div className="flex items-center gap-3 flex-wrap">
                <span className="heading text-[12px] uppercase tracking-widest text-white">
                    {result.protocol?.toUpperCase()}://{result.host}{result.port ? `:${result.port}` : ""}
                </span>
                <span
                    className="label text-[9px] uppercase border px-1"
                    style={{ color, borderColor: color + "60" }}
                >
                    {result.status}
                </span>
                {result.latency_ms != null && (
                    <span className="label text-[9px] text-[#888]">
                        {result.latency_ms}ms
                    </span>
                )}
                {d.dns_ip && (
                    <span className="label text-[9px] text-[#888]">dns: {d.dns_ip}</span>
                )}
                {onRemove && (
                    <button
                        onClick={onRemove}
                        className="ml-auto text-[#555] hover:text-[#FF2A2A]"
                        data-testid={`server-remove-${result.host}`}
                    >
                        <Trash2 size={11} />
                    </button>
                )}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3 text-[10px]">
                <Metric label="tcp" value={d.tcp_ok ? "OK" : "BLOCKED"} color={d.tcp_ok ? "#CCFF00" : "#FF2A2A"} />
                {d.tcp_latency_ms != null && <Metric label="tcp lat" value={`${d.tcp_latency_ms}ms`} />}
                {d.http_ok != null && (
                    <Metric label="http" value={d.http_ok ? "OK" : "FAIL"} color={d.http_ok ? "#CCFF00" : "#FF2A2A"} />
                )}
                {d.http_info?.status && <Metric label="status" value={d.http_info.status} />}
                {d.http_info?.server && <Metric label="server" value={d.http_info.server} />}
                {d.tcp_error && <Metric label="error" value={d.tcp_error} color="#FF2A2A" />}
            </div>
            {result.status === "GATED" && (
                <div className="mt-2 text-[10px] text-[#FF8800] flex items-center gap-1">
                    <ShieldAlert size={11} />
                    {d.note || "gated — operator cryptographic approval required."}
                </div>
            )}
            {result.timestamp && (
                <div className="text-[9px] text-[#555] mt-2">
                    probed {new Date(result.timestamp).toLocaleString()}
                </div>
            )}
        </div>
    );
};

const Metric = ({ label, value, color }) => (
    <div className="border border-white/5 px-2 py-1">
        <div className="label text-[8px] text-[#666] uppercase">{label}</div>
        <div className="font-mono" style={{ color: color || "#fff" }}>{value}</div>
    </div>
);

export default ServerScreen;
