// NeuralInterfaceScreen — ANIP/1.0 BCI deck.
// Acquire (synthetic or EDF upload) → decode (band power, spikes, fusion)
// → verifiable substrate runs (lattice energy / LIF propagation / attention).
import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { API } from "@/App";

const NEON = "#CCFF00";
const CYAN = "#00E5FF";
const MAGENTA = "#FF2A88";
const BAND_COLORS = {
    delta: "#A29BFE", theta: "#00E5FF", alpha: "#CCFF00",
    beta: "#FF2A88", gamma: "#FF8800",
};

const WaveCanvas = ({ channels, spikes }) => {
    const ref = useRef(null);
    useEffect(() => {
        const cv = ref.current;
        if (!cv || !channels?.length) return;
        const ctx = cv.getContext("2d");
        const W = (cv.width = cv.clientWidth * 2);
        const H = (cv.height = cv.clientHeight * 2);
        ctx.fillStyle = "#000";
        ctx.fillRect(0, 0, W, H);
        const rowH = H / channels.length;
        channels.forEach((ch, ci) => {
            const xs = ch.samples;
            if (!xs?.length) return;
            const max = Math.max(...xs.map(Math.abs)) || 1;
            ctx.strokeStyle = ci % 2 ? CYAN : NEON;
            ctx.globalAlpha = 0.9;
            ctx.lineWidth = 1.4;
            ctx.beginPath();
            const y0 = rowH * ci + rowH / 2;
            for (let i = 0; i < xs.length; i++) {
                const x = (i / xs.length) * W;
                const y = y0 - (xs[i] / max) * (rowH * 0.42);
                i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
            }
            ctx.stroke();
            // spike markers
            const sp = spikes?.[ci]?.times_ms || [];
            const durMs = (xs.length / (spikes?.fs || 256)) * 1000;
            ctx.fillStyle = MAGENTA;
            sp.forEach((t) => {
                const x = (t / (durMs || 1)) * W;
                ctx.fillRect(x, rowH * ci + 2, 3, 8);
            });
            ctx.fillStyle = "#888";
            ctx.font = "18px monospace";
            ctx.fillText(ch.label || `ch${ci}`, 8, rowH * ci + 22);
            ctx.globalAlpha = 1;
        });
    }, [channels, spikes]);
    return (
        <canvas
            ref={ref}
            className="w-full h-full block"
            data-testid="bci-wave-canvas"
        />
    );
};

const EnergySpark = ({ traj }) => {
    if (!traj?.length) return null;
    const min = Math.min(...traj), max = Math.max(...traj);
    const pts = traj
        .map((e, i) => {
            const x = (i / (traj.length - 1 || 1)) * 100;
            const y = 30 - ((e - min) / (max - min || 1)) * 28;
            return `${x},${y}`;
        })
        .join(" ");
    return (
        <svg viewBox="0 0 100 32" className="w-full h-8" data-testid="bci-energy-spark">
            <polyline points={pts} fill="none" stroke={NEON} strokeWidth="1.2" />
        </svg>
    );
};

const Check = ({ ok, label }) => (
    <div className="flex items-center gap-2 text-[10px] font-mono">
        <span style={{ color: ok ? NEON : "#FF2A2A" }}>{ok ? "✓" : "✗"}</span>
        <span className="text-[#999]">{label}</span>
    </div>
);

export default function NeuralInterfaceScreen() {
    const [protocol, setProtocol] = useState(null);
    const [state, setState] = useState("focus");
    const [acq, setAcq] = useState(null);
    const [decode, setDecode] = useState(null);
    const [substrate, setSubstrate] = useState(null);
    const [busy, setBusy] = useState("");
    const [err, setErr] = useState("");

    useEffect(() => {
        axios.get(`${API}/neural/protocol`).then((r) => setProtocol(r.data)).catch(() => {});
    }, []);

    const acquire = async () => {
        setBusy("acquiring");
        setErr("");
        try {
            const r = await axios.post(`${API}/neural/synthetic`, {
                state, seconds: 2, fs: 256, channels: 8, decode: true,
            });
            setAcq(r.data);
            setDecode(r.data.decode || null);
        } catch (e) {
            setErr(e.response?.data?.detail || e.message);
        } finally {
            setBusy("");
        }
    };

    const uploadEdf = async (file) => {
        if (!file) return;
        setBusy("parsing edf");
        setErr("");
        try {
            const buf = await file.arrayBuffer();
            let bin = "";
            const bytes = new Uint8Array(buf);
            for (let i = 0; i < bytes.length; i += 8192) {
                bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
            }
            const r = await axios.post(`${API}/neural/edf/parse`, {
                b64: btoa(bin), decode: true,
            });
            setAcq({ acquisition: `EDF ${r.data.format}`, fs: r.data.fs, channels: r.data.channels });
            setDecode(r.data.decode || null);
        } catch (e) {
            setErr(e.response?.data?.detail || e.message);
        } finally {
            setBusy("");
        }
    };

    const runSubstrate = async (kind) => {
        setBusy(kind);
        setErr("");
        try {
            let r;
            if (kind === "lattice") {
                r = await axios.post(`${API}/neural/substrate/lattice-energy`, { n: 32, steps: 64 });
            } else if (kind === "propagate") {
                r = await axios.post(`${API}/neural/substrate/propagate`, { n_neurons: 16, duration_ms: 300 });
            } else {
                const m = decode
                    ? decode.channels.map((c) => Object.values(c.band_power.relative))
                    : [[0.2, 0.2, 0.3, 0.2, 0.1], [0.1, 0.2, 0.4, 0.2, 0.1]];
                r = await axios.post(`${API}/neural/substrate/fuse`, { matrix: m, n_heads: 4 });
            }
            setSubstrate({ kind, data: r.data });
        } catch (e) {
            setErr(e.response?.data?.detail || e.message);
        } finally {
            setBusy("");
        }
    };

    const spikesByCh = decode
        ? Object.assign(decode.channels.map((c) => c.spikes), { fs: acq?.fs })
        : null;

    return (
        <div className="h-full flex flex-col overflow-hidden" data-testid="bci-screen">
            {/* protocol strip */}
            <div className="px-3 py-2 border-b border-white/10 flex items-center gap-3 flex-wrap">
                <span className="heading text-[10px] tracking-widest uppercase" style={{ color: NEON }}>
                    ANIP/1.0
                </span>
                <span className="text-[9px] font-mono text-[#888]">
                    EDF/EDF+ · IEEE-2731 vocab · 10-20 montage · Quiroga MAD spikes
                </span>
                <span className="ml-auto text-[9px] font-mono" style={{ color: CYAN }}>
                    {protocol ? "protocol loaded" : "loading protocol…"}
                </span>
            </div>

            <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-5 gap-2 p-2 overflow-y-auto althea-scroll">
                {/* LEFT — acquisition + waveforms */}
                <div className="lg:col-span-3 flex flex-col gap-2 min-h-0">
                    <div className="border border-white/10 p-2 flex items-center gap-2 flex-wrap">
                        <select
                            value={state}
                            onChange={(e) => setState(e.target.value)}
                            data-testid="bci-state-select"
                            className="bg-black border border-white/20 text-[11px] font-mono px-2 py-1 text-white"
                        >
                            <option value="rest">rest (alpha)</option>
                            <option value="focus">focus (beta)</option>
                            <option value="drowsy">drowsy (theta)</option>
                            <option value="motor-left">motor-imagery left</option>
                            <option value="motor-right">motor-imagery right</option>
                        </select>
                        <button
                            onClick={acquire}
                            disabled={!!busy}
                            data-testid="bci-acquire-btn"
                            className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#CCFF00]/50 text-[#CCFF00] hover:bg-[#CCFF00]/10"
                        >
                            {busy === "acquiring" ? "acquiring…" : "acquire + decode"}
                        </button>
                        <label className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#00E5FF]/40 text-[#00E5FF] hover:bg-[#00E5FF]/10 cursor-pointer">
                            upload edf
                            <input
                                type="file"
                                accept=".edf,.bdf,.rec"
                                className="hidden"
                                data-testid="bci-edf-input"
                                onChange={(e) => uploadEdf(e.target.files?.[0])}
                            />
                        </label>
                        {err && (
                            <span className="text-[10px] font-mono text-[#FF2A2A]" data-testid="bci-error">
                                {String(err).slice(0, 90)}
                            </span>
                        )}
                    </div>

                    <div className="flex-1 min-h-[220px] border border-white/10 relative">
                        {acq?.channels?.length ? (
                            <WaveCanvas channels={acq.channels} spikes={spikesByCh} />
                        ) : (
                            <div className="absolute inset-0 flex items-center justify-center text-[11px] font-mono text-[#666]">
                                no signal — acquire synthetic EEG or upload an EDF recording
                            </div>
                        )}
                    </div>

                    {/* substrate row */}
                    <div className="border border-white/10 p-2">
                        <div className="label text-[9px] text-[#888] uppercase tracking-widest mb-2">
                            verifiable substrate engines
                        </div>
                        <div className="flex gap-2 flex-wrap">
                            <button onClick={() => runSubstrate("lattice")} disabled={!!busy}
                                data-testid="bci-lattice-btn"
                                className="text-[10px] font-mono px-2 py-1 border border-white/20 text-[#CCFF00] hover:bg-white/5">
                                lattice-energy
                            </button>
                            <button onClick={() => runSubstrate("propagate")} disabled={!!busy}
                                data-testid="bci-propagate-btn"
                                className="text-[10px] font-mono px-2 py-1 border border-white/20 text-[#00E5FF] hover:bg-white/5">
                                differential-propagation
                            </button>
                            <button onClick={() => runSubstrate("fuse")} disabled={!!busy}
                                data-testid="bci-fuse-btn"
                                className="text-[10px] font-mono px-2 py-1 border border-white/20 text-[#FF2A88] hover:bg-white/5">
                                transformer-fusion
                            </button>
                        </div>
                        {substrate && (
                            <div className="mt-2 text-[10px] font-mono text-[#bbb]" data-testid="bci-substrate-result">
                                <div className="text-[#CCFF00]">
                                    {substrate.data.engine} · checksum {substrate.data.verification?.checksum}
                                </div>
                                {substrate.kind === "lattice" && (
                                    <>
                                        <EnergySpark traj={substrate.data.energy_trajectory} />
                                        <div>
                                            E {substrate.data.initial_energy} → {substrate.data.final_energy}
                                            {" "}(released {substrate.data.energy_released}) ·
                                            {" "}{substrate.data.spin_flips} flips · converged sweep {String(substrate.data.converged_at_sweep)}
                                        </div>
                                    </>
                                )}
                                {substrate.kind === "propagate" && (
                                    <div>
                                        {substrate.data.total_spikes} spikes · mean rate {substrate.data.mean_rate_hz} Hz ·
                                        {" "}{substrate.data.n_neurons} LIF neurons · dt {substrate.data.dt_ms} ms
                                    </div>
                                )}
                                {substrate.kind === "fuse" && (
                                    <div>
                                        {substrate.data.n_heads} heads · d_model {substrate.data.d_model} ·
                                        {" "}attention entropy {substrate.data.attention_entropy_nats} nats
                                    </div>
                                )}
                                <div className="mt-1 grid grid-cols-2 gap-x-3">
                                    {(substrate.data.verification?.checks || []).map((c) => (
                                        <Check key={c.name} ok={c.passed} label={c.name} />
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* RIGHT — decode results */}
                <div className="lg:col-span-2 flex flex-col gap-2 min-h-0">
                    <div className="border border-white/10 p-3" data-testid="bci-decoded-state">
                        <div className="label text-[9px] text-[#888] uppercase tracking-widest mb-1">
                            decoded state
                        </div>
                        {decode ? (
                            <>
                                <div className="heading text-sm" style={{ color: NEON }}>
                                    {decode.decoded_state}
                                </div>
                                <div className="text-[10px] font-mono text-[#999] mt-1">
                                    confidence {Math.round(decode.confidence * 100)}% ·
                                    {" "}{decode.evidence?.[0]}
                                </div>
                            </>
                        ) : (
                            <div className="text-[11px] font-mono text-[#666]">awaiting signal</div>
                        )}
                    </div>

                    {decode && (
                        <>
                            <div className="border border-white/10 p-3">
                                <div className="label text-[9px] text-[#888] uppercase tracking-widest mb-2">
                                    mean relative band power
                                </div>
                                {Object.entries(decode.mean_relative_power).map(([band, v]) => (
                                    <div key={band} className="flex items-center gap-2 mb-1">
                                        <span className="text-[9px] font-mono w-10 text-[#999]">{band}</span>
                                        <div className="flex-1 h-2 bg-white/5">
                                            <div
                                                className="h-full"
                                                style={{ width: `${Math.min(v * 100, 100)}%`, background: BAND_COLORS[band] }}
                                            />
                                        </div>
                                        <span className="text-[9px] font-mono text-[#777] w-10 text-right">
                                            {(v * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                ))}
                            </div>

                            <div className="border border-white/10 p-3">
                                <div className="label text-[9px] text-[#888] uppercase tracking-widest mb-2">
                                    transformer-fusion attention (channels)
                                </div>
                                <div
                                    className="grid gap-[2px]"
                                    style={{ gridTemplateColumns: `repeat(${decode.fusion.attention.length}, 1fr)` }}
                                    data-testid="bci-attention-grid"
                                >
                                    {decode.fusion.attention.flat().map((v, i) => (
                                        <div
                                            key={i}
                                            className="aspect-square"
                                            style={{ background: `rgba(204,255,0,${Math.min(v * 2.2, 1)})` }}
                                            title={v.toFixed(3)}
                                        />
                                    ))}
                                </div>
                                <div className="text-[9px] font-mono text-[#777] mt-1">
                                    entropy {decode.fusion.entropy_nats} nats · lattice released
                                    {" "}{decode.lattice.energy_released} E
                                </div>
                                <EnergySpark traj={decode.lattice.energy_trajectory} />
                            </div>

                            <div className="border border-white/10 p-3" data-testid="bci-verification">
                                <div className="label text-[9px] text-[#888] uppercase tracking-widest mb-2">
                                    verification —{" "}
                                    <span style={{ color: decode.verification.all_passed ? NEON : "#FF2A2A" }}>
                                        {decode.verification.all_passed ? "ALL INVARIANTS HOLD" : "VIOLATIONS FOUND"}
                                    </span>
                                </div>
                                {(decode.verification.fusion_checks?.checks || []).map((c) => (
                                    <Check key={`f-${c.name}`} ok={c.passed} label={`fusion · ${c.name}`} />
                                ))}
                                {(decode.verification.lattice_checks?.checks || []).map((c) => (
                                    <Check key={`l-${c.name}`} ok={c.passed} label={`lattice · ${c.name}`} />
                                ))}
                                <Check ok={decode.verification.psd_nonnegative} label="psd_nonnegative" />
                                <Check ok={decode.verification.relative_power_normalized} label="relative_power_normalized" />
                            </div>

                            <div className="border border-white/10 p-3">
                                <div className="label text-[9px] text-[#888] uppercase tracking-widest mb-2">
                                    per-channel spikes (Quiroga 4.5σ MAD)
                                </div>
                                {decode.channels.map((c) => (
                                    <div key={c.label} className="text-[9px] font-mono text-[#999] flex justify-between">
                                        <span>{c.label}</span>
                                        <span>
                                            {c.spikes.count} spikes · thr {c.spikes.threshold}µV · σ {c.spikes.sigma_mad}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
