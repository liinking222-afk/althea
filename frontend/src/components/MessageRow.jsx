// MessageRow — terminal message with rich rendering.
// Renders LaTeX math (KaTeX), fenced code blocks, **bold**, and embedded
// [IMAGE: ...] directives (which fetch a Gemini-generated image inline).
// Unlimited length: just streams whatever Althea writes verbatim.
import React, { useEffect, useState } from "react";
import katex from "katex";
import axios from "axios";
import { API } from "@/App";
import { Copy, Check, RefreshCw } from "lucide-react";
import { TAG_COLOR, getMessageTag } from "@/lib/terminalConstants";

const downloadText = (name, content) => {
    const blob = new Blob([content], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
};

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
        // 1: letter body      2: blueprint title  3: blueprint body
        // 4: synth image src  5: image directive  6: fenced code lang
        // 7: fenced code body 8: block math       9: inline math
        // 10: bold
        /\[LETTER\]([\s\S]*?)\[\/LETTER\]|\[BLUEPRINT:?\s*([^\]]*)\]([\s\S]*?)\[\/BLUEPRINT\]|\[SYNTH-IMAGE:\s*([^\]]+)\]|\[IMAGE:\s*([^\]]+)\]|```([a-zA-Z0-9_+-]*)\n?([\s\S]*?)```|\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$|\*\*([^*]+)\*\*/g;
    let cursor = 0;
    let m;
    while ((m = re.exec(text)) !== null) {
        if (m.index > cursor) {
            tokens.push({ type: "text", value: text.slice(cursor, m.index) });
        }
        if (m[0].startsWith("[LETTER]")) {
            tokens.push({ type: "letter", value: (m[1] || "").trim() });
        } else if (m[0].startsWith("[BLUEPRINT")) {
            tokens.push({
                type: "blueprint",
                title: (m[2] || "UNTITLED").trim() || "UNTITLED",
                value: (m[3] || "").trim(),
            });
        } else if (m[0].startsWith("[SYNTH-IMAGE:")) {
            tokens.push({ type: "synth-image", src: m[4].trim() });
        } else if (m[0].startsWith("[IMAGE:")) {
            tokens.push({ type: "image", prompt: m[5].trim() });
        } else if (m[0].startsWith("```")) {
            tokens.push({
                type: "code",
                lang: (m[6] || "").trim(),
                value: m[7] ?? "",
            });
        } else if (m[0].startsWith("$$")) {
            tokens.push({ type: "math-block", value: m[8] });
        } else if (m[0].startsWith("$")) {
            tokens.push({ type: "math-inline", value: m[9] });
        } else if (m[0].startsWith("**")) {
            tokens.push({ type: "bold", value: m[10] });
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
                if (t.type === "letter")
                    return (
                        <div key={i} className="my-3 max-w-[580px] letter-paper" data-testid="letter-doc">
                            <div className="flex items-center justify-between px-4 pt-3">
                                <span className="tracking-[0.3em] text-[9px] uppercase text-[#8a7b5c] font-mono">
                                    althea // correspondence
                                </span>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => navigator.clipboard?.writeText(t.value)}
                                        data-testid="letter-copy-btn"
                                        className="doc-btn"
                                    >
                                        copy
                                    </button>
                                    <button
                                        onClick={() => downloadText(`althea-letter-${Date.now()}.txt`, t.value)}
                                        data-testid="letter-download-btn"
                                        className="doc-btn"
                                    >
                                        download
                                    </button>
                                </div>
                            </div>
                            <div className="letter-body px-5 py-4 whitespace-pre-wrap">{t.value}</div>
                            <div className="px-4 pb-3 text-right text-[9px] tracking-[0.25em] uppercase text-[#8a7b5c] font-mono">
                                — sovereign cognition core
                            </div>
                        </div>
                    );
                if (t.type === "blueprint") {
                    const schemMatch = t.value.match(/\[SCHEMATIC-IMAGE:([^\]]+)\]/);
                    const bodyText = t.value.replace(/\n?\[SCHEMATIC-IMAGE:[^\]]+\]\n?/, "\n");
                    return (
                        <div key={i} className="my-3 blueprint-sheet" data-testid="blueprint-doc">
                            <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-[#4FA3FF]/40 flex-wrap">
                                <span className="heading text-[10px] tracking-widest uppercase text-[#9CCBFF]">
                                    ⌗ blueprint // {t.title}
                                </span>
                                <div className="flex gap-2 items-center">
                                    <span className="text-[8px] font-mono text-[#4FA3FF]">
                                        REV A · {new Date().toISOString().slice(0, 10)}
                                    </span>
                                    <button
                                        onClick={() =>
                                            downloadText(
                                                `blueprint-${t.title.replace(/\s+/g, "-").toLowerCase()}.txt`,
                                                bodyText,
                                            )
                                        }
                                        data-testid="blueprint-download-btn"
                                        className="doc-btn doc-btn-blue"
                                    >
                                        download
                                    </button>
                                </div>
                            </div>
                            {schemMatch && (
                                <div className="px-3 pt-3">
                                    <img
                                        src={schemMatch[1]}
                                        alt="drawn schematic"
                                        className="w-full max-w-[540px] border border-[#4FA3FF]/30"
                                        data-testid="blueprint-schematic-img"
                                    />
                                    <div className="text-[8px] font-mono text-[#4FA3FF] mt-1 tracking-widest uppercase">
                                        schematic drawn by self-grown engine · 0 credits
                                    </div>
                                </div>
                            )}
                            <pre className="blueprint-body px-4 py-3 whitespace-pre-wrap">{bodyText}</pre>
                        </div>
                    );
                }
                if (t.type === "synth-image")
                    return (
                        <div
                            key={i}
                            className="my-2 border border-[#CCFF00]/40 bg-black p-1.5 inline-block max-w-full"
                            data-testid="synth-image"
                        >
                            <div className="label text-[9px] text-[#CCFF00] mb-1 tracking-widest uppercase">
                                autosynth // self-grown render
                            </div>
                            <img
                                src={t.src}
                                alt="autosynth render"
                                className="block max-w-[440px] max-h-[440px] w-auto h-auto"
                                data-testid="synth-image-img"
                            />
                        </div>
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

const MessageRow = ({ m, onRegenerate }) => {
    const isUser = m.role === "user";
    const inlineTag = getMessageTag(m.content);
    const primaryTag =
        (m.tags && m.tags[0]) ||
        (inlineTag && TAG_COLOR[inlineTag] ? inlineTag : null);
    const color = primaryTag && TAG_COLOR[primaryTag];
    const isBanner = primaryTag === "BANNER";
    const [copied, setCopied] = useState(false);

    const doCopy = async () => {
        try {
            await navigator.clipboard.writeText(m.content || "");
            setCopied(true);
            setTimeout(() => setCopied(false), 1400);
        } catch {
            setCopied(false);
        }
    };

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
            className="fade-up pl-2 border-l-2 group relative"
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
                {m.restored && (
                    <span
                        className="border border-[#666]/40 px-1 text-[#666]"
                        title="restored from previous session"
                    >
                        RESTORED
                    </span>
                )}
                {/* actions — visible on hover on desktop, always visible on mobile */}
                <span className="ml-auto flex items-center gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                    <button
                        onClick={doCopy}
                        data-testid={`msg-copy-${m.id || "row"}`}
                        title="copy message"
                        className="p-1 hover:text-[#CCFF00]"
                    >
                        {copied ? <Check size={10} /> : <Copy size={10} />}
                    </button>
                    {!isUser && onRegenerate && (
                        <button
                            onClick={() => onRegenerate(m)}
                            data-testid={`msg-regen-${m.id || "row"}`}
                            title="regenerate althea's reply"
                            className="p-1 hover:text-[#FF2A88]"
                        >
                            <RefreshCw size={10} />
                        </button>
                    )}
                </span>
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
