import React, { useEffect, useRef, useState } from "react";
import { ArrowLeft, Send, Users } from "lucide-react";

const time = (ts) => {
    try { return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); } catch { return ""; }
};

export const DmTerminal = ({ me, peer, messages, onSend, onBack }) => {
    const [text, setText] = useState("");
    const [busy, setBusy] = useState(false);
    const endRef = useRef(null);
    const human = messages.filter((m) => m.kind === "human" || m.kind === "ask");

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [human.length]);

    const send = async (e) => {
        e?.preventDefault();
        const content = text.trim();
        if (!content || busy) return;
        setBusy(true);
        try {
            await onSend(content);
            setText("");
        } finally {
            setBusy(false);
        }
    };

    return (
        <div className="flex flex-col h-full" data-testid="dm-terminal">
            <div className="flex items-center gap-2 pb-2 border-b border-white/10">
                <button onClick={onBack} className="text-[#666] hover:text-[#CCFF00]" data-testid="dm-back-btn" title="back to your althea">
                    <ArrowLeft size={13} />
                </button>
                <Users size={12} className="text-[#CCFF00]" />
                <span className="label text-[10px] uppercase tracking-widest text-[#CCFF00]">
                    direct line // {peer?.name || "…"}
                </span>
                {peer?.online && <span className="w-1.5 h-1.5 rounded-full bg-[#48FFB0]" />}
                <div className="flex-1" />
                <span className="label text-[9px] text-[#555] font-mono">@{peer?.handle}</span>
            </div>

            <div className="flex-1 overflow-y-auto althea-scroll py-3 space-y-2 pr-1" data-testid="dm-messages">
                {human.length === 0 && (
                    <div className="text-[11px] text-[#666] font-mono leading-snug">
                        private line open. type to {peer?.name}. mention <span className="text-[#CCFF00]">@althea</span> to pull the shared mind in — she is listening either way.
                    </div>
                )}
                {human.map((m) => {
                    const mine = m.sender_id === me?.user_id;
                    return (
                        <div key={m.id} className={`flex ${mine ? "justify-end" : "justify-start"}`} data-testid={`dm-msg-${m.id}`}>
                            <div
                                className={`max-w-[85%] px-3 py-2 border text-[12px] leading-snug whitespace-pre-wrap break-words ${
                                    mine
                                        ? "border-[#CCFF00]/40 bg-[#CCFF00]/5 text-white"
                                        : "border-white/15 bg-[#0A0A0A] text-white/90"
                                }`}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="label text-[9px] uppercase tracking-wider" style={{ color: mine ? "#CCFF00" : "#00F0FF" }}>
                                        {mine ? "you" : m.sender_name}
                                    </span>
                                    {m.kind === "ask" && <span className="label text-[8px] uppercase text-[#FF2A88]">→ althea</span>}
                                    <span className="text-[8px] text-[#555] font-mono ml-auto">{time(m.timestamp)}</span>
                                </div>
                                {m.content}
                            </div>
                        </div>
                    );
                })}
                <div ref={endRef} />
            </div>

            <form onSubmit={send} className="flex items-center gap-2 border border-white/15 px-2 py-1.5 focus-within:border-[#CCFF00]/60">
                <input
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder={`message ${peer?.name || ""}… (@althea to call her)`}
                    className="flex-1 bg-transparent text-[12px] font-mono outline-none"
                    data-testid="dm-input"
                />
                <button type="submit" disabled={busy || !text.trim()} className="text-[#CCFF00] disabled:opacity-30" data-testid="dm-send-btn">
                    <Send size={13} />
                </button>
            </form>
        </div>
    );
};

export default DmTerminal;
