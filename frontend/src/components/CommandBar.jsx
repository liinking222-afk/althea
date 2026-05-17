import React, { useEffect, useState } from "react";

const CommandBar = ({ online, introspection, permissions }) => {
    const [now, setNow] = useState(new Date());
    useEffect(() => {
        const t = setInterval(() => setNow(new Date()), 1000);
        return () => clearInterval(t);
    }, []);

    const grantedCount =
        Object.values(permissions).filter(Boolean).length;

    return (
        <footer
            className="border-t border-white/10 px-4 py-2 flex items-center justify-between text-[10px] heading uppercase tracking-widest text-[#888]"
            data-testid="command-bar"
        >
            <div className="flex items-center gap-6">
                <span className="flex items-center gap-2">
                    <span
                        className={`dot ${online ? "" : "alert"}`}
                    />
                    {online ? "uplink stable" : "offline · cached"}
                </span>
                <span>
                    bridge:{" "}
                    <span className="text-[#CCFF00]">
                        {grantedCount}/6 grants
                    </span>
                </span>
                <span className="hidden md:inline">
                    self-aware:{" "}
                    <span className="text-[#CCFF00]">
                        {introspection
                            ? `depth ${introspection.self_reference_depth}`
                            : "..."}
                    </span>
                </span>
            </div>

            {/* center waveform */}
            <div
                className="flex items-end gap-[2px] h-6"
                data-testid="audio-visualizer"
            >
                {Array.from({ length: 14 }).map((_, i) => (
                    <span
                        key={i}
                        className="wave-bar"
                        style={{ animationDelay: `${(i % 7) * 0.08}s` }}
                    />
                ))}
            </div>

            <div className="flex items-center gap-6">
                <span>
                    utc{" "}
                    <span className="text-white">
                        {now.toISOString().slice(11, 19)}
                    </span>
                </span>
                <span>
                    althea {" "}
                    <span className="text-[#CCFF00]">v0.9-alpha</span>
                </span>
            </div>
        </footer>
    );
};

export default CommandBar;
