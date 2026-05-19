// MessageRow — single terminal line. Extracted from ChatConsole.jsx (P2 refactor).
import React from "react";
import { TAG_COLOR, getMessageTag } from "@/lib/terminalConstants";

const MessageRow = ({ m }) => {
    const isUser = m.role === "user";
    const inlineTag = getMessageTag(m.content);
    const primaryTag =
        (m.tags && m.tags[0]) ||
        (inlineTag && TAG_COLOR[inlineTag] ? inlineTag : null);
    const color = primaryTag && TAG_COLOR[primaryTag];
    const isBanner = primaryTag === "BANNER";

    if (isBanner) {
        return (
            <pre
                className="fade-up font-mono text-[10px] leading-tight text-[#FF2A88] glow whitespace-pre"
                data-testid="ascii-banner"
            >
                {m.content}
            </pre>
        );
    }

    return (
        <div
            className="fade-up pl-2 border-l-2"
            style={{
                borderLeftColor: isUser ? "#444" : color || "#CCFF00",
            }}
        >
            <div className="label text-[9px] mb-1 flex items-center gap-2">
                <span style={{ color: isUser ? "#888" : color || "#CCFF00" }}>
                    {isUser ? "operator" : "althea"}
                </span>
                {m.tags?.map((t) => (
                    <span
                        key={t}
                        className="border px-1"
                        style={{
                            color: TAG_COLOR[t] || "#666",
                            borderColor: (TAG_COLOR[t] || "#666") + "40",
                        }}
                    >
                        {t}
                    </span>
                ))}
            </div>
            <div
                className="text-[12px] leading-relaxed whitespace-pre-wrap"
                style={{
                    color: isUser
                        ? "rgba(255,255,255,0.9)"
                        : "rgba(255,255,255,0.92)",
                }}
            >
                {m.content}
            </div>
        </div>
    );
};

export default MessageRow;
