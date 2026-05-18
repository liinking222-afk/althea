import React from "react";

const TopBar = ({ online, sessionId, onReset, introspection }) => {
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
                            sovereign cognition // v0.9-alpha
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

            <div className="flex items-center gap-6">
                <Metric label="integrity" value={`${integrity}%`} />
                <Metric label="coherence" value={`${coherence}%`} />
                <Metric
                    label="link"
                    value={online ? "ONLINE" : "OFFLINE"}
                    accent={!online}
                />
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
