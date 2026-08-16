import React from "react";
import MiniMap from "@/components/MiniMap";
import PermissionsPanel from "@/components/PermissionsPanel";
import WorkerCoresPanel from "@/components/WorkerCoresPanel";

const TelemetryPanel = ({ online, geo, permissions, togglePermission }) => {
    return (
        <section
            className="h-full flex flex-col gap-3 min-h-0"
            data-testid="telemetry-panel"
        >
            {/* GPS / Map */}
            <div className="panel cut flex-1 min-h-0 flex flex-col overflow-hidden relative grain">
                <header className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                    <div className="flex items-center gap-2">
                        <div
                            className={`dot ${geo ? "" : "idle"}`}
                        />
                        <h3 className="heading text-sm tracking-widest uppercase">
                            public gps // openstreetmap
                        </h3>
                    </div>
                    <span className="label text-[9px]">
                        {geo ? "lock" : "no-lock"}
                    </span>
                </header>
                <div className="flex-1 min-h-0 relative">
                    <MiniMap geo={geo} />
                    {!geo && (
                        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                            <div className="text-center">
                                <div className="label text-[10px] mb-1">
                                    awaiting gps lock
                                </div>
                                <div className="text-[#666] text-[11px]">
                                    grant geolocation in permissions panel
                                </div>
                            </div>
                        </div>
                    )}
                </div>
                {geo && (
                    <div className="px-4 py-2 border-t border-white/10 flex justify-between text-[10px] text-[#888] heading uppercase tracking-widest">
                        <span>
                            lat <span className="text-white">{geo.lat.toFixed(4)}</span>
                        </span>
                        <span>
                            lon <span className="text-white">{geo.lon.toFixed(4)}</span>
                        </span>
                        <span>
                            ±<span className="text-white">{Math.round(geo.acc)}m</span>
                        </span>
                    </div>
                )}
            </div>

            {/* 8-core worker mesh */}
            <WorkerCoresPanel />

            {/* Permissions */}
            <PermissionsPanel
                permissions={permissions}
                togglePermission={togglePermission}
            />

            {/* Network status */}
            <div className="panel cut p-4" data-testid="network-status">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="heading text-sm tracking-widest uppercase">
                        uplink
                    </h3>
                    <span
                        className={`label text-[9px] ${online ? "text-[#CCFF00]" : "text-[#FF2A2A]"}`}
                    >
                        {online ? "online" : "offline"}
                    </span>
                </div>
                <div className="flex items-end gap-1 h-8">
                    {Array.from({ length: 22 }).map((_, i) => {
                        const h = online
                            ? 6 + Math.abs(Math.sin(i * 1.3) * 22)
                            : 4 + (i % 3) * 2;
                        return (
                            <div
                                key={i}
                                style={{ height: `${h}px` }}
                                className={`w-1 ${online ? "bg-[#CCFF00]" : "bg-[#FF2A2A]"} opacity-${i % 3 === 0 ? "100" : "60"}`}
                            />
                        );
                    })}
                </div>
                <div className="mt-2 text-[10px] text-[#888]">
                    {online
                        ? "starlink-class mesh stable · 12ms · 99.9%"
                        : "uplink lost · operating from cached lattice"}
                </div>
            </div>
        </section>
    );
};

export default TelemetryPanel;
