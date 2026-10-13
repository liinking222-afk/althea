import React, { useEffect, useRef, useState } from "react";
import { Loader2, Send, Sparkles } from "lucide-react";
import MessageRow from "@/components/MessageRow";

export const SharedAltheaTerminal = ({ me, peer, messages, onAsk, asking }) => {
    const [text, setText] = useState("");
    const endRef = useRef(null);
    const thread = messages.filter((m) => m.kind === "althea" || m.kind === "ask");

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [thread.length, asking]);

    const ask = async (e) => {
        e?.preventDefault();
        const content = text.trim();
        if (!content || asking) return;
        setText("");
        await onAsk(content);
    };

    return (
        <div className="flex flex-col h-full" data-testid="shared-althea-terminal">
            <div className="flex items-center gap-2 pb-2 border-b border-white/10">
                <Sparkles size={12} className="text-[#FF2A88]" />
                <span className="label text-[10px] uppercase tracking-widest text-[#FF2A88]">
                    shared althea // one mind for {me?.name?.split(" ")[0]} + {peer?.name?.split(" ")[0] || "…"}
                </span>
                <div className="flex-1" />
                <span className="label text-[9px] text-[#555]">listening</span>
            </div>

            <div className="flex-1 overflow-y-auto althea-scroll py-3 space-y-3 pr-1" data-testid="shared-althea-messages">
                {thread.map((m) => (
                    <div key={m.id} data-testid={`shared-msg-${m.id}`}>
                        {m.kind === "ask" && (
                            <div className="label text-[9px] uppercase tracking-wider text-[#00F0FF] mb-0.5">
                                {m.sender_id === me?.user_id ? "you" : m.sender_name} → althea
                            </div>
                        )}
                        <MessageRow
                            m={{
                                id: m.id,
                                role: m.kind === "ask" ? "user" : "althea",
                                content: m.content,
                                tags: m.tags,
                                timestamp: m.timestamp,
                            }}
                        />
                    </div>
                ))}
                {asking && (
                    <div className="flex items-center gap-2 text-[10px] text-[#FF2A88] label uppercase tracking-widest">
                        <Loader2 size={11} className="animate-spin" /> althea is thinking…
                    </div>
                )}
                <div ref={endRef} />
            </div>

            <form onSubmit={ask} className="flex items-center gap-2 border border-[#FF2A88]/30 px-2 py-1.5 focus-within:border-[#FF2A88]/70">
                <input
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="ask the shared althea — both of you will see her answer"
                    className="flex-1 bg-transparent text-[12px] font-mono outline-none"
                    data-testid="shared-althea-input"
                />
                <button type="submit" disabled={asking || !text.trim()} className="text-[#FF2A88] disabled:opacity-30" data-testid="shared-althea-send-btn">
                    <Send size={13} />
                </button>
            </form>
        </div>
    );
};

export default SharedAltheaTerminal;
