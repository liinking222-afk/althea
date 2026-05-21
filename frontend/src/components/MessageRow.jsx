// MessageRow — terminal message with rich rendering.
// Renders LaTeX math (KaTeX), fenced code blocks, **bold**, and embedded
// [IMAGE: ...] directives (which fetch a Gemini-generated image inline).
// Unlimited length: just streams whatever Althea writes verbatim.
import React, { useEffect, useState } from "react";
import katex from "katex";
import axios from "axios";
import { API } from "@/App";
import { TAG_COLOR, getMessageTag } from "@/lib/terminalConstants";

// --- LaTeX renderer (sandboxed katex call with graceful fallback) ---
const renderMath = (tex, displayMode) => {
    try {
        return katex.renderToString(tex, {
            displayMode,
            throwOnError: false,
            output: "html",
            strict: "warn",
        });
    } catch {
        return `<span class="text-[#FF2A88]">[math-err: ${tex.slice(0, 40)}]</span>`;
    }
};

// --- Tokenizer: split the message into typed segments ---
const tokenize = (text) => {
    if (!text) return [];
    const tokens = [];
    // We do a single-pass scan with a master regex that captures the first
    // occurrence of any rich block.
    const re =
        // 1: image directive  2: fenced code lang  3: fenced code body
        // 4: block math       5: inline math
        // 6: bold
        /\[IMAGE:\s*([^\]]+)\]|```([a-zA-Z0-9_+-]*)\n?([\s\S]*?)```|\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$|\*\*([^*]+)\*\*/g;
    let cursor = 0;
    let m;
    while ((m = re.exec(text)) !== null) {
        if (m.index > cursor) {
            tokens.push({ type: "text", value: text.slice(cursor, m.index) });
        }
        if (m[0].startsWith("[IMAGE:")) {
            tokens.push({ type: "image", prompt: m[1].trim() });
        } else if (m[0].startsWith("```")) {
            tokens.push({
                type: "code",
                lang: (m[2] || "").trim(),
                value: m[3] ?? "",
            });
        } else if (m[0].startsWith("$$")) {
            tokens.push({ type: "math-block", value: m[4] });
        } else if (m[0].startsWith("$")) {
            tokens.push({ type: "math-inline", value: m[5] });
        } else if (m[0].startsWith("**")) {
            tokens.push({ type: "bold", value: m[6] });
        }
        cursor = m.index + m[0].length;
    }
    if (cursor < text.length) {
        tokens.push({ type: "text", value: text.slice(cursor) });
    }
    return tokens;
};

// --- Image directive component: lazily fetches a Gemini render ---
const InlineImage = ({ prompt, messageId, index }) => {
    const [src, setSrc] = useState(null);
    const [err, setErr] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        const cacheKey = `althea_img__${messageId}__${index}`;
        const cached = sessionStorage.getItem(cacheKey);
        if (cached) {
            setSrc(cached);
            setLoading(false);
            return;
        }
        (async () => {
            try {
                const res = await axios.post(`${API}/images/generate`, {
                    prompt,
                    purpose: "explanation",
                });
                if (cancelled) return;
                setSrc(res.data.data_url);
                try {
                    sessionStorage.setItem(cacheKey, res.data.data_url);
                } catch (_e) {
                    // sessionStorage may be full; harmless to skip caching
                }
            } catch (e) {
                if (cancelled) return;
                setErr(e.response?.data?.detail || e.message);
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [prompt, messageId, index]);

    return (
        <div
            className="my-2 border border-[#FF2A88]/40 bg-black p-1.5 inline-block max-w-full"
            data-testid={`inline-image-${index}`}
        >
            <div className="label text-[9px] text-[#FF2A88] mb-1 tracking-widest uppercase">
                rendered // {loading ? "synthesizing" : err ? "failed" : "althea visual"}
            </div>
            {loading && (
                <div className="text-[11px] text-[#888] font-mono p-3">
                    [GEMINI-NANO-BANANA] painting "{prompt.slice(0, 50)}{prompt.length > 50 ? "…" : ""}"
                </div>
            )}
            {err && (
                <div className="text-[11px] text-[#FF2A88] font-mono p-3">
                    image-fail: {err.slice(0, 120)}
                </div>
            )}
            {src && (
                <img
                    src={src}
                    alt={prompt}
                    className="block max-w-[440px] max-h-[440px] w-auto h-auto"
                    data-testid={`inline-image-${index}-img`}
                />
            )}
            <div className="text-[9px] text-[#666] mt-1 font-mono">
                prompt: {prompt.slice(0, 200)}
            </div>
        </div>
    );
};

const RichContent = ({ content, messageId }) => {
    const tokens = tokenize(content);
    let imgIdx = 0;
    return (
        <div className="text-[12px] md:text-[13px] leading-relaxed whitespace-pre-wrap break-words">
            {tokens.map((t, i) => {
                if (t.type === "text") return <span key={i}>{t.value}</span>;
                if (t.type === "bold")
                    return (
                        <strong key={i} className="text-white font-semibold">
                            {t.value}
                        </strong>
                    );
                if (t.type === "math-inline")
                    return (
                        <span
                            key={i}
                            className="text-[#CCFF00]"
                            dangerouslySetInnerHTML={{
                                __html: renderMath(t.value, false),
                            }}
                        />
                    );
                if (t.type === "math-block")
                    return (
                        <div
                            key={i}
                            className="my-2 py-2 px-3 border-l-2 border-[#CCFF00]/40 bg-[#CCFF00]/[0.03] overflow-x-auto text-[#CCFF00]"
                            data-testid="math-block"
                            dangerouslySetInnerHTML={{
                                __html: renderMath(t.value, true),
                            }}
                        />
                    );
                if (t.type === "code")
                    return (
                        <pre
                            key={i}
                            className="my-2 p-2 bg-black border border-white/15 text-[#00F0FF] font-mono text-[11.5px] overflow-x-auto whitespace-pre"
                            data-testid="code-block"
                        >
                            {t.lang && (
                                <div className="label text-[8px] text-[#666] mb-1">
                                    {t.lang}
                                </div>
                            )}
                            {t.value}
                        </pre>
                    );
                if (t.type === "image") {
                    const i2 = imgIdx++;
                    return (
                        <InlineImage
                            key={i}
                            prompt={t.prompt}
                            messageId={messageId || "msg"}
                            index={i2}
                        />
                    );
                }
                return null;
            })}
        </div>
    );
};

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
            data-testid={`message-${isUser ? "user" : "althea"}`}
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
                style={{
                    color: isUser
                        ? "rgba(255,255,255,0.9)"
                        : "rgba(255,255,255,0.92)",
                }}
            >
                <RichContent content={m.content || ""} messageId={m.id} />
            </div>
        </div>
    );
};

export default MessageRow;
