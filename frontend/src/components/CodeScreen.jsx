import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Code2, Loader2, Play, Trash2, Download, Copy, Check } from "lucide-react";

const LANGS = ["python", "javascript", "typescript", "bash", "rust", "go", "html", "css"];

const CodeScreen = () => {
    const [intent, setIntent] = useState("");
    const [language, setLanguage] = useState("python");
    const [busy, setBusy] = useState(false);
    const [list, setList] = useState([]);
    const [selected, setSelected] = useState(null);
    const [copied, setCopied] = useState(false);

    const refresh = useCallback(async () => {
        try {
            const r = await axios.get(`${API}/code`);
            setList(r.data || []);
            if (selected) {
                const fresh = (r.data || []).find((c) => c.id === selected.id);
                if (fresh) setSelected(fresh);
            }
        } catch (_) {/* ignore */}
    }, [selected]);

    useEffect(() => {
        refresh();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const generate = async (e) => {
        e?.preventDefault?.();
        if (!intent.trim() || busy) return;
        setBusy(true);
        try {
            const r = await axios.post(`${API}/code/generate`, {
                intent: intent.trim(),
                language,
            });
            setSelected(r.data);
            setIntent("");
            await refresh();
        } catch (e) {
            console.warn("code gen failed:", e);
        } finally {
            setBusy(false);
        }
    };

    const apply = async (id) => {
        try {
            const r = await axios.post(`${API}/code/apply`, { id });
            await refresh();
            return r.data;
        } catch (_) {/* ignore */}
    };

    const removeOne = async (id) => {
        await axios.delete(`${API}/code/${id}`);
        if (selected?.id === id) setSelected(null);
        await refresh();
    };

    const copy = async () => {
        if (!selected?.code) return;
        try {
            await navigator.clipboard.writeText(selected.code);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        } catch (_) {/* ignore */}
    };

    const download = () => {
        if (!selected) return;
        const ext = {
            python: "py", javascript: "js", typescript: "ts",
            bash: "sh", rust: "rs", go: "go", html: "html", css: "css",
        }[selected.language] || "txt";
        const blob = new Blob([selected.code], { type: "text/plain" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `${selected.id.slice(0, 8)}-${selected.title.replace(/[^a-z0-9]+/gi, "_")}.${ext}`;
        a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    };

    return (
        <div className="w-full h-full flex flex-col text-white" data-testid="code-screen">
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2">
                <Code2 size={13} className="text-[#CCFF00]" />
                <h3 className="heading text-[11px] uppercase tracking-widest text-[#CCFF00]">
                    self-write // althea authors code for herself
                </h3>
                <span className="label text-[9px] text-[#666]">{list.length} snippets</span>
            </div>

            <form onSubmit={generate} className="px-4 py-3 border-b border-white/10 flex items-center gap-2 flex-wrap bg-[#0A0A0A]">
                <input
                    value={intent}
                    onChange={(e) => setIntent(e.target.value)}
                    placeholder="intent — e.g. 'a websocket relay that broadcasts heartbeats every 5s'"
                    className="flex-1 min-w-[260px] bg-transparent border border-white/15 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#CCFF00]/60"
                    data-testid="code-intent-input"
                />
                <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="bg-[#080808] border border-white/15 px-2 py-1 text-[11px] font-mono outline-none focus:border-[#CCFF00]/60"
                    data-testid="code-language-select"
                >
                    {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
                </select>
                <button
                    type="submit"
                    disabled={busy || !intent.trim()}
                    data-testid="code-generate-btn"
                    className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#CCFF00]/60 text-[#CCFF00] hover:bg-[#CCFF00]/10 disabled:opacity-40 flex items-center gap-1"
                >
                    {busy ? <Loader2 size={11} className="animate-spin" /> : <Code2 size={11} />}
                    write code
                </button>
            </form>

            <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 min-h-0">
                <div className="overflow-y-auto althea-scroll p-2 space-y-1 border-r border-white/10">
                    <div className="label text-[9px] uppercase text-[#666] px-2 py-1">snippets</div>
                    {list.length === 0 && (
                        <div className="text-[10px] text-[#555] px-2">no snippets yet.</div>
                    )}
                    {list.map((c) => (
                        <button
                            key={c.id}
                            onClick={() => setSelected(c)}
                            data-testid={`code-item-${c.id}`}
                            className={`block w-full text-left px-2 py-2 border ${selected?.id === c.id ? "border-[#CCFF00]/60 bg-[#CCFF00]/5" : "border-transparent hover:border-white/20"}`}
                        >
                            <div className="text-[10px] heading uppercase tracking-widest text-[#CCFF00] truncate">
                                {c.title}
                            </div>
                            <div className="text-[9px] text-[#666] truncate">
                                {c.language} · {c.code.length}c · {c.applied ? "applied" : "draft"}
                            </div>
                        </button>
                    ))}
                </div>

                <div className="lg:col-span-3 flex flex-col min-h-0">
                    {!selected && (
                        <div className="flex-1 flex items-center justify-center text-[#666] text-[11px] heading uppercase tracking-widest">
                            select a snippet or write a new one.
                        </div>
                    )}
                    {selected && (
                        <>
                            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2 flex-wrap">
                                <span className="heading text-sm uppercase tracking-widest text-[#CCFF00]">
                                    {selected.title}
                                </span>
                                <span className="label text-[9px] uppercase border border-[#CCFF00]/40 text-[#CCFF00] px-1">
                                    {selected.language}
                                </span>
                                {selected.applied && (
                                    <span className="label text-[9px] uppercase border border-[#00F0FF]/40 text-[#00F0FF] px-1">
                                        applied
                                    </span>
                                )}
                                <div className="flex-1" />
                                <button
                                    onClick={copy}
                                    data-testid="code-copy-btn"
                                    className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-white/15 hover:border-[#CCFF00]/60 hover:text-[#CCFF00] flex items-center gap-1"
                                >
                                    {copied ? <Check size={11} /> : <Copy size={11} />}
                                    {copied ? "copied" : "copy"}
                                </button>
                                <button
                                    onClick={download}
                                    data-testid="code-download-btn"
                                    className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-white/15 hover:border-[#CCFF00]/60 hover:text-[#CCFF00] flex items-center gap-1"
                                >
                                    <Download size={11} /> save
                                </button>
                                <button
                                    onClick={() => apply(selected.id)}
                                    data-testid="code-apply-btn"
                                    className="heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#FF2A88]/60 text-[#FF2A88] hover:bg-[#FF2A88]/10 flex items-center gap-1"
                                >
                                    <Play size={11} /> apply
                                </button>
                                <button
                                    onClick={() => removeOne(selected.id)}
                                    data-testid="code-delete-btn"
                                    className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-[#FF2A2A]/40 text-[#FF2A2A] hover:bg-[#FF2A2A]/10"
                                >
                                    <Trash2 size={11} />
                                </button>
                            </div>
                            <div className="px-4 py-2 text-[10px] text-[#888] italic border-b border-white/5">
                                intent: {selected.intent}
                            </div>
                            <pre
                                data-testid="code-content"
                                className="flex-1 overflow-auto althea-scroll p-4 text-[11px] font-mono text-white/90 whitespace-pre bg-[#050505]"
                            >
                                {selected.code}
                            </pre>
                            {selected.explanation && (
                                <div className="border-t border-white/10 p-3 text-[10px] text-[#aaa] leading-snug max-h-32 overflow-y-auto bg-[#080808]">
                                    <span className="text-[#CCFF00]">› althea: </span>{selected.explanation}
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CodeScreen;
