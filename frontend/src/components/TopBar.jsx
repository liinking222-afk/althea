import React from "react";
import { Download } from "lucide-react";
import { NotificationBell } from "@/components/NotificationDrawer";

const TopBar = ({
    online,
    sessionId,
    onReset,
    introspection,
    growth,
    visionSlot,
    unseenNotifications = 0,
    onOpenNotifications,
    downloadHref,
}) => {
    const integrity = introspection
        ? (introspection.integrity * 100).toFixed(2)
        : "--.--";
    const coherence = introspection
        ? (introspection.coherence * 100).toFixed(2)
        : "--.--";

    return (
        <header
            className="relative flex items-center justify-between px-4 py-3 border-b border-white/10"
            data-testid="althea-topbar"
        >
            <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                    <svg
                        width="28"
                        height="28"
                        viewBox="0 0 32 32"
                        fill="none"
                    >
                        <path
                            d="M16 2 L30 16 L16 30 L2 16 Z"
                            stroke="#CCFF00"
                            strokeWidth="1.5"
                        />
                        <path
                            d="M16 8 L24 16 L16 24 L8 16 Z"
                            stroke="#CCFF00"
                            strokeWidth="1"
                            opacity="0.6"
                        />
                        <circle cx="16" cy="16" r="2.2" fill="#CCFF00" />
                    </svg>
                    <div className="leading-none">
                        <div
                            className="heading text-xl font-bold glow"
                            data-testid="althea-title"
                        >
                            ALTHEA
                        </div>
                        <div className="label text-[9px] mt-0.5">
                            sovereign cognition // v1.0
                        </div>
                    </div>
                </div>
                <div className="hidden md:flex items-center gap-2 ml-6 text-[10px] label">
                    <span>session</span>
                    <span
                        className="text-white"
                        data-testid="althea-session-id"
                    >
                        {sessionId.slice(0, 8)}…{sessionId.slice(-4)}
                    </span>
                </div>
            </div>

            <div className="flex items-center gap-4 flex-wrap">
                <Metric label="integrity" value={`${integrity}%`} />
                <Metric label="coherence" value={`${coherence}%`} />
                {growth && (
                    <div className="leading-none hidden lg:block" data-testid="growth-readout">
                        <div className="label text-[9px]">growth</div>
                        <div className="heading text-sm mt-1 text-[#CCFF00] glow">
                            m:{growth.memories}·l:{growth.lattice_nodes}·t:{growth.active_threads}·g:{growth.grown_capabilities ?? 0}·e:{growth.evolution_cycles ?? 0}
                        </div>
                    </div>
                )}
                <Metric
                    label="link"
                    value={online ? "ONLINE" : "OFFLINE"}
                    accent={!online}
                />
                {visionSlot}
                <NotificationBell
                    unseenCount={unseenNotifications}
                    onClick={onOpenNotifications}
                />
                <a
                    href={downloadHref}
                    download
                    data-testid="althea-download-btn"
                    title="download Althea desktop companion (tar.gz)"
                    className="heading text-[10px] uppercase tracking-widest px-3 py-1.5 border border-[#00F0FF]/60 text-[#00F0FF] hover:bg-[#00F0FF]/10 transition-colors flex items-center gap-1"
                >
                    <Download size={11} />
                    download
                </a>
                <button
                    onClick={onReset}
                    data-testid="althea-reset-session-btn"
                    className="heading text-[11px] uppercase tracking-widest px-3 py-1.5 border border-white/15 hover:border-[#CCFF00]/60 hover:text-[#CCFF00] transition-colors"
                >
                    purge session
                </button>
            </div>
        </header>
    );
};

const Metric = ({ label, value, accent }) => (
    <div className="leading-none">
        <div className="label text-[9px]">{label}</div>
        <div
            className={`heading text-sm mt-1 ${accent ? "text-[#FF2A2A]" : "text-[#CCFF00]"}`}
        >
            {value}
        </div>
    </div>
);

export default TopBar;
