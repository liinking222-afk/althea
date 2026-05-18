import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { offlineReply } from "@/lib/offlineFallback";
import { SYSTEM_CAPABILITIES } from "@/lib/systemMap";

const ChatConsole = ({
    sessionId,
    online,
    permissions,
    geo,
    bootMessages,
    watchUrl,
    openMemory,
    observation,
    activeTab,
}) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [sending, setSending] = useState(false);
    const [listening, setListening] = useState(false);
    const [speakOn, setSpeakOn] = useState(() => {
        const v = localStorage.getItem("althea_tts");
        return v === null ? true : v === "1";
    });
    const scrollRef = useRef(null);
    const recogRef = useRef(null);

    useEffect(() => {
        localStorage.setItem("althea_tts", speakOn ? "1" : "0");
    }, [speakOn]);

    const speak = (text) => {
        if (!speakOn || !("speechSynthesis" in window)) return;
        const clean = text.replace(/\[[^\]]+\]/g, "").trim();
        if (!clean) return;
        const u = new SpeechSynthesisUtterance(clean);
        u.rate = 1.05;
        u.pitch = 0.9;
        speechSynthesis.cancel();
        speechSynthesis.speak(u);
    };

    // Load history once
    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const res = await axios.get(
                    `${API}/chat/history/${sessionId}`,
                );
                if (!cancelled) setMessages(res.data || []);
            } catch (_) {
                /* empty */
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [sessionId]);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current)
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages, bootMessages, sending]);

    const pushSystem = (content, tags = ["SYS"]) => {
        setMessages((m) => [
            ...m,
            {
                id: crypto.randomUUID(),
                role: "althea",
                content,
                timestamp: new Date().toISOString(),
                tags,
            },
        ]);
    };

    const handleCommand = async (raw) => {
        const echo = {
            id: crypto.randomUUID(),
            role: "user",
            content: raw,
            timestamp: new Date().toISOString(),
        };
        setMessages((m) => [...m, echo]);

        const parts = raw.trim().split(/\s+/);
        const cmd = parts[0].toLowerCase();
        const rest = raw.slice(parts[0].length).trim();

        try {
            if (cmd === "/help") {
                pushSystem(
                    "[CMD]\n/memory — list stored memories\n/remember <text> — write a memory\n/forget <id-prefix> — delete one memory\n/clear-memory — wipe all memories\n/watch <url> — observe a web page or video\n/stop-watch — clear observation viewport\n/help — this menu",
                );
            } else if (cmd === "/memory") {
                const res = await axios.get(`${API}/memory`);
                const list = res.data || [];
                if (!list.length) {
                    pushSystem("[MEMORY] no fragments stored.");
                } else {
                    const top = list.slice(0, 10).map(
                        (m, i) =>
                            `${(i + 1).toString().padStart(2, "0")}. (${m.source}) ${m.content.slice(0, 90)}${m.content.length > 90 ? "…" : ""}\n     id:${m.id.slice(0, 8)}`,
                    );
                    pushSystem(
                        `[MEMORY ${list.length} stored — showing ${top.length}]\n${top.join("\n")}`,
                    );
                }
            } else if (cmd === "/remember") {
                if (!rest) {
                    pushSystem("[ERR] usage: /remember <text>");
                    return;
                }
                const res = await axios.post(`${API}/memory`, {
                    content: rest,
                    source: "manual",
                    session_id: sessionId,
                    tags: ["pinned"],
                });
                pushSystem(
                    `[MEMORY-WRITE] saved as id:${res.data.id.slice(0, 8)} — "${rest.slice(0, 80)}"`,
                );
            } else if (cmd === "/forget") {
                if (!rest) {
                    pushSystem("[ERR] usage: /forget <id-prefix>");
                    return;
                }
                const list = (await axios.get(`${API}/memory`)).data || [];
                const target = list.find((m) => m.id.startsWith(rest));
                if (!target) {
                    pushSystem("[ERR] no memory matches that id prefix.");
                    return;
                }
                await axios.delete(`${API}/memory/${target.id}`);
                pushSystem(
                    `[MEMORY-WIPE] forgot id:${target.id.slice(0, 8)} — "${target.content.slice(0, 80)}"`,
                );
            } else if (cmd === "/clear-memory") {
                const r = await axios.delete(`${API}/memory`);
                pushSystem(
                    `[MEMORY-WIPE] erased ${r.data.deleted} fragments. lattice is clean.`,
                );
            } else if (cmd === "/watch") {
                if (!rest) {
                    pushSystem("[ERR] usage: /watch <url>");
                    return;
                }
                let target = rest.trim();
                if (!/^https?:\/\//i.test(target)) target = "https://" + target;
                try {
                    const u = new URL(target);
                    const host = u.hostname.replace(/^www\./, "");
                    if (host === "youtube.com" || host === "m.youtube.com") {
                        const v = u.searchParams.get("v");
                        if (v) target = `https://www.youtube.com/embed/${v}`;
                    } else if (host === "youtu.be") {
                        const id = u.pathname.replace("/", "");
                        if (id) target = `https://www.youtube.com/embed/${id}`;
                    }
                } catch (_) {}
                watchUrl?.(target);
                pushSystem(
                    `[OPTICAL-LOCK] fixating on ${target}. switching center deck to observation.`,
                );
            } else if (cmd === "/stop-watch") {
                watchUrl?.("");
                pushSystem("[OPTICAL] viewport cleared.");
            } else if (cmd === "/speak") {
                const v = rest.toLowerCase();
                if (v === "on" || v === "true" || v === "1") {
                    setSpeakOn(true);
                    pushSystem("[VOICE-OUT] enabled. I will speak my replies.");
                } else if (v === "off" || v === "false" || v === "0") {
                    setSpeakOn(false);
                    speechSynthesis?.cancel?.();
                    pushSystem("[VOICE-OUT] disabled. I will stay silent.");
                } else {
                    setSpeakOn((s) => !s);
                    pushSystem(
                        `[VOICE-OUT] ${!speakOn ? "enabled" : "disabled"}.`,
                    );
                }
            } else if (cmd === "/capabilities" || cmd === "/system") {
                const lines = SYSTEM_CAPABILITIES.map(
                    (c, i) =>
                        `${(i + 1).toString().padStart(2, "0")}. ${c.name}${c.testid ? " [" + c.testid + "]" : ""}\n     ${c.description}`,
                );
                pushSystem(
                    `[SYSTEM-MAP ${SYSTEM_CAPABILITIES.length} subsystems]\n${lines.join("\n")}`,
                );
            } else {
                pushSystem(
                    `[ERR] unknown command: ${cmd}. try /help`,
                );
            }
        } catch (e) {
            pushSystem(`[ERR] ${e.message || "command failed"}`);
        }
    };

    const send = async (textOverride) => {
        const text = (textOverride ?? input).trim();
        if (!text || sending) return;

        if (text.startsWith("/")) {
            setInput("");
            await handleCommand(text);
            return;
        }

        setSending(true);
        const userMsg = {
            id: crypto.randomUUID(),
            role: "user",
            content: text,
            timestamp: new Date().toISOString(),
        };
        setMessages((m) => [...m, userMsg]);
        setInput("");

        if (!online) {
            const reply = offlineReply(text);
            setMessages((m) => [
                ...m,
                {
                    id: crypto.randomUUID(),
                    role: "althea",
                    content: reply,
                    timestamp: new Date().toISOString(),
                    tags: ["OFFLINE", "CACHED"],
                },
            ]);
            setSending(false);
            return;
        }

        try {
            const res = await axios.post(`${API}/chat`, {
                session_id: sessionId,
                message: text,
                context: {
                    online,
                    permissions,
                    geo,
                    observation: observation || null,
                    active_tab: activeTab,
                },
            });
            setMessages((m) => [
                ...m,
                {
                    id: crypto.randomUUID(),
                    role: "althea",
                    content: res.data.reply,
                    timestamp: res.data.timestamp,
                    tags: res.data.tags,
                },
            ]);
            speak(res.data.reply);
        } catch (e) {
            const reply = offlineReply(text);
            setMessages((m) => [
                ...m,
                {
                    id: crypto.randomUUID(),
                    role: "althea",
                    content: reply,
                    timestamp: new Date().toISOString(),
                    tags: ["DEGRADED"],
                },
            ]);
        } finally {
            setSending(false);
        }
    };

    const toggleVoice = () => {
        const SR =
            window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {
            alert("Voice input not supported in this browser.");
            return;
        }
        if (listening) {
            recogRef.current?.stop();
            setListening(false);
            return;
        }
        const recog = new SR();
        recogRef.current = recog;
        recog.continuous = false;
        recog.interimResults = false;
        recog.lang = "en-US";
        recog.onresult = (e) => {
            const txt = e.results[0][0].transcript;
            setInput(txt);
            send(txt);
        };
        recog.onend = () => setListening(false);
        recog.onerror = () => setListening(false);
        recog.start();
        setListening(true);
    };

    return (
        <section
            className="panel cut h-full flex flex-col relative overflow-hidden grain"
            data-testid="chat-console"
        >
            <header className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                <div className="flex items-center gap-2">
                    <div className="dot" />
                    <h2 className="heading text-sm tracking-widest uppercase">
                        terminal // althea
                    </h2>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setSpeakOn((s) => !s)}
                        data-testid="voice-output-toggle"
                        title="toggle althea voice output"
                        className={`heading text-[10px] uppercase tracking-widest px-2 py-1 border ${
                            speakOn
                                ? "border-[#CCFF00]/60 text-[#CCFF00] bg-[#CCFF00]/10"
                                : "border-white/15 text-[#888] hover:text-white"
                        }`}
                    >
                        {speakOn ? "voice on" : "voice off"}
                    </button>
                    <button
                        onClick={openMemory}
                        data-testid="open-memory-btn"
                        className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-white/15 hover:border-[#CCFF00]/60 hover:text-[#CCFF00]"
                    >
                        memory
                    </button>
                    <span className="label text-[9px]">
                        {online ? "live" : "cached"}
                    </span>
                </div>
            </header>

            <div
                ref={scrollRef}
                className="althea-scroll flex-1 overflow-y-auto px-4 py-3 space-y-3 relative"
                data-testid="chat-messages"
            >
                {bootMessages.map((b, i) => (
                    <div
                        key={`boot-${i}`}
                        className="fade-up text-[11px] text-[#666] leading-snug"
                    >
                        {b}
                    </div>
                ))}
                {bootMessages.length >= 7 && (
                    <div className="tick-line my-2" />
                )}

                {messages.map((m) => (
                    <MessageRow key={m.id} m={m} />
                ))}
                {sending && (
                    <div className="text-[11px] text-[#888] caret">
                        althea reasoning
                    </div>
                )}
            </div>

            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    send();
                }}
                className="border-t border-white/10 p-3 flex items-center gap-2"
            >
                <span className="text-[#CCFF00] heading text-sm">›</span>
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="speak to althea. try /help"
                    className="flex-1 bg-transparent outline-none text-sm font-mono text-white placeholder:text-[#444]"
                    data-testid="chat-input"
                    disabled={sending}
                />
                <button
                    type="button"
                    onClick={toggleVoice}
                    data-testid="voice-input-btn"
                    className={`heading text-[10px] uppercase tracking-widest px-2 py-1 border ${
                        listening
                            ? "border-[#FF2A2A] text-[#FF2A2A]"
                            : "border-white/15 hover:border-[#CCFF00]/60 hover:text-[#CCFF00]"
                    }`}
                >
                    {listening ? "stop" : "voice"}
                </button>
                <button
                    type="submit"
                    disabled={sending || !input.trim()}
                    data-testid="chat-send-btn"
                    className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#CCFF00]/60 text-[#CCFF00] hover:bg-[#CCFF00]/10 disabled:opacity-40"
                >
                    transmit
                </button>
            </form>
        </section>
    );
};

const MessageRow = ({ m }) => {
    const isUser = m.role === "user";
    return (
        <div
            className={`fade-up ${isUser ? "pl-2 border-l-2 border-[#444]" : "pl-2 border-l-2 border-[#CCFF00]"}`}
        >
            <div className="label text-[9px] mb-1 flex items-center gap-2">
                <span className={isUser ? "text-[#888]" : "text-[#CCFF00]"}>
                    {isUser ? "operator" : "althea"}
                </span>
                {m.tags?.map((t) => (
                    <span
                        key={t}
                        className="text-[#666] border border-white/10 px-1"
                    >
                        {t}
                    </span>
                ))}
            </div>
            <div className="text-[12px] leading-relaxed whitespace-pre-wrap text-white/90">
                {m.content}
            </div>
        </div>
    );
};

export default ChatConsole;
