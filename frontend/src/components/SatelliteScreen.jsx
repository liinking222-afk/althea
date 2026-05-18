import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { API } from "@/App";
import { Satellite, Signal, ArrowDownUp } from "lucide-react";

/**
 * Satellite mesh — equirectangular world projection with orbiting sats.
 * Constellations pulse in distinct colors. Click a sat to lock telemetry.
 */
const SatelliteScreen = () => {
    const [feed, setFeed] = useState(null);
    const [locked, setLocked] = useState(null);
    const svgRef = useRef(null);

    useEffect(() => {
        let cancelled = false;
        const tick = async () => {
            try {
                const r = await axios.get(`${API}/satellite/feed`);
                if (!cancelled) setFeed(r.data);
            } catch (_) {/* ignore */}
        };
        tick();
        const t = setInterval(tick, 2000);
        return () => { cancelled = true; clearInterval(t); };
    }, []);

    const project = (lat, lon) => {
        // Equirectangular: x ∈ [0, W], y ∈ [0, H]
        const W = 1000;
        const H = 500;
        return {
            x: ((lon + 180) / 360) * W,
            y: ((90 - lat) / 180) * H,
        };
    };

    const metrics = feed?.metrics || {};
    const sats = feed?.satellites || [];
    const constellations = feed?.constellations || [];

    return (
        <div className="w-full h-full flex flex-col text-white" data-testid="satellite-screen">
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-3 flex-wrap">
                <Satellite size={14} className="text-[#A29BFE]" />
                <h3 className="heading text-[11px] uppercase tracking-widest text-[#A29BFE]">
                    satellite mesh // low-earth-orbit uplink
                </h3>
                <div className="flex-1" />
                <Stat label="sats" value={metrics.total ?? "-"} />
                <Stat label="locked" value={metrics.locked ?? "-"} color="#CCFF00" />
                <Stat label="signal" value={metrics.avg_signal != null ? `${(metrics.avg_signal * 100).toFixed(0)}%` : "-"} color="#00F0FF" />
                <Stat label="integrity" value={metrics.mesh_integrity != null ? `${(metrics.mesh_integrity * 100).toFixed(1)}%` : "-"} color="#A29BFE" />
            </div>

            <div className="px-4 py-2 border-b border-white/5 flex items-center gap-4 text-[10px] bg-[#0A0A0A]">
                <span className="flex items-center gap-1 text-[#aaa]">
                    <ArrowDownUp size={10} className="text-[#CCFF00]" />
                    UP {((metrics.uplink_bps || 0) / 1_000_000).toFixed(2)} Mbps
                </span>
                <span className="flex items-center gap-1 text-[#aaa]">
                    <ArrowDownUp size={10} className="text-[#00F0FF]" />
                    DN {((metrics.downlink_bps || 0) / 1_000_000).toFixed(2)} Mbps
                </span>
                <div className="flex-1" />
                {constellations.map((c) => (
                    <span key={c.name} className="flex items-center gap-1 label text-[9px]" style={{ color: c.color }}>
                        <span
                            className="w-2 h-2 rounded-full inline-block"
                            style={{ background: c.color, boxShadow: `0 0 6px ${c.color}` }}
                        />
                        {c.name}
                    </span>
                ))}
            </div>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 min-h-0">
                <div className="lg:col-span-3 relative bg-[#020208] overflow-hidden">
                    <svg
                        ref={svgRef}
                        viewBox="0 0 1000 500"
                        preserveAspectRatio="xMidYMid meet"
                        className="absolute inset-0 w-full h-full"
                        data-testid="satellite-map"
                    >
                        {/* Grid */}
                        <defs>
                            <pattern id="latlon" width="50" height="50" patternUnits="userSpaceOnUse">
                                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#A29BFE" strokeWidth="0.4" opacity="0.08" />
                            </pattern>
                            <radialGradient id="satGlow">
                                <stop offset="0%" stopColor="#fff" stopOpacity="1" />
                                <stop offset="100%" stopColor="#fff" stopOpacity="0" />
                            </radialGradient>
                        </defs>
                        <rect width="1000" height="500" fill="url(#latlon)" />
                        {/* Equator + meridian */}
                        <line x1="0" y1="250" x2="1000" y2="250" stroke="#A29BFE" strokeWidth="0.5" opacity="0.2" />
                        <line x1="500" y1="0" x2="500" y2="500" stroke="#A29BFE" strokeWidth="0.5" opacity="0.2" />
                        {/* Constellation orbital rings (illustrative arcs) */}
                        {constellations.map((c, i) => (
                            <ellipse
                                key={c.name}
                                cx="500" cy="250" rx="430" ry={120 + i * 30}
                                fill="none" stroke={c.color} strokeWidth="0.5" opacity="0.18"
                                strokeDasharray="4 6"
                            />
                        ))}
                        {/* Satellites */}
                        {sats.map((s) => {
                            const { x, y } = project(s.lat, s.lon);
                            const r = 2 + s.signal * 3;
                            return (
                                <g
                                    key={s.id}
                                    onClick={() => setLocked(s)}
                                    style={{ cursor: "pointer" }}
                                    data-testid={`sat-${s.id}`}
                                >
                                    <circle cx={x} cy={y} r={r * 2.4} fill={s.color} opacity={0.15} />
                                    <circle cx={x} cy={y} r={r} fill={s.color} opacity={0.4 + s.signal * 0.5} />
                                    {locked?.id === s.id && (
                                        <circle cx={x} cy={y} r={r + 6} fill="none" stroke={s.color} strokeWidth="1" />
                                    )}
                                </g>
                            );
                        })}
                        {/* Locked sat ground-link */}
                        {locked && (
                            <line
                                x1={project(locked.lat, locked.lon).x}
                                y1={project(locked.lat, locked.lon).y}
                                x2="500" y2="250"
                                stroke={locked.color}
                                strokeWidth="0.6"
                                opacity="0.55"
                                strokeDasharray="2 3"
                            />
                        )}
                    </svg>
                    <div className="absolute bottom-2 left-3 label text-[9px] text-[#666]">
                        equirectangular projection · click a satellite to lock telemetry
                    </div>
                </div>

                <div className="overflow-y-auto althea-scroll p-3 border-l border-white/10 bg-[#050505]">
                    <div className="label text-[9px] uppercase text-[#A29BFE] mb-2">
                        telemetry · {locked ? locked.id : "select a sat"}
                    </div>
                    {!locked && (
                        <div className="text-[10px] text-[#555]">
                            no satellite locked. click any orbiting dot.
                        </div>
                    )}
                    {locked && (
                        <div className="space-y-2 text-[11px]" data-testid="sat-telemetry">
                            <Row label="constellation" value={locked.constellation} color={locked.color} />
                            <Row label="altitude" value={`${locked.altitude_km} km`} />
                            <Row label="lat / lon" value={`${locked.lat.toFixed(3)} / ${locked.lon.toFixed(3)}`} />
                            <Row label="signal" value={`${(locked.signal * 100).toFixed(0)}%`} color="#CCFF00" />
                            <Row label="phase" value={locked.phase.toFixed(3)} />
                            <div className="flex items-center gap-2 mt-3 pt-3 border-t border-white/5">
                                <Signal size={10} className="text-[#CCFF00]" />
                                <span className="label text-[9px]">
                                    {locked.signal > 0.85 ? "LOCKED · LOS" : locked.signal > 0.6 ? "TRACKING" : "WEAK"}
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

const Stat = ({ label, value, color }) => (
    <div className="leading-none">
        <div className="label text-[9px] uppercase text-[#666]">{label}</div>
        <div className="heading text-sm mt-0.5" style={{ color: color || "#fff" }}>{value}</div>
    </div>
);

const Row = ({ label, value, color }) => (
    <div className="flex items-center justify-between border-b border-white/5 pb-1">
        <span className="label text-[9px] uppercase text-[#666]">{label}</span>
        <span className="font-mono" style={{ color: color || "#fff" }}>{value}</span>
    </div>
);

export default SatelliteScreen;
