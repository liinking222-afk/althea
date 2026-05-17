import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { offlineReply } from "@/lib/offlineFallback";

const ChatConsole = ({ sessionId, online, permissions, geo, bootMessages }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [sending, setSending] = useState(false);
    const [listening, setListening] = useState(false);
    const scrollRef = useRef(null);
    const recogRef = useRef(null);

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

    const send = async (textOverride) => {
        const text = (textOverride ?? input).trim();
        if (!text || sending) return;
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
                context: { online, permissions, geo },
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
            // speak if microphone permission active (voice mode)
            if (permissions.microphone && "speechSynthesis" in window) {
                const u = new SpeechSynthesisUtterance(
                    res.data.reply.replace(/\[[^\]]+\]/g, ""),
                );
                u.rate = 1.05;
                u.pitch = 0.9;
                speechSynthesis.cancel();
                speechSynthesis.speak(u);
            }
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
                <span className="label text-[9px]">
                    {online ? "live" : "cached"}
                </span>
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
                    placeholder="speak to althea..."
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
