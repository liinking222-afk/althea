import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { Trash2, X } from "lucide-react";
import { API } from "@/App";

const MemoryDrawer = ({ open, onClose }) => {
    const [memories, setMemories] = useState([]);
    const [loading, setLoading] = useState(false);
    const [query, setQuery] = useState("");

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const res = await axios.get(`${API}/memory`);
            setMemories(res.data || []);
        } catch (_) {
            setMemories([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (open) load();
    }, [open, load]);

    const removeOne = async (id) => {
        try {
            await axios.delete(`${API}/memory/${id}`);
            setMemories((m) => m.filter((x) => x.id !== id));
        } catch (_) {}
    };

    const wipeAll = async () => {
        if (!window.confirm("Erase ALL of Althea's long-term memories?")) return;
        try {
            await axios.delete(`${API}/memory`);
            setMemories([]);
        } catch (_) {}
    };

    if (!open) return null;

    const filtered = query
        ? memories.filter((m) =>
              m.content.toLowerCase().includes(query.toLowerCase()),
          )
        : memories;

    return (
        <div
            className="fixed inset-0 z-50 flex justify-end bg-black/70 backdrop-blur-sm"
            data-testid="memory-drawer"
            onClick={(e) => {
                if (e.target === e.currentTarget) onClose();
            }}
        >
            <aside className="h-full w-full max-w-2xl bg-[#0A0A0A] border-l border-white/10 flex flex-col relative grain">
                <header className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
                    <div>
                        <div className="heading text-lg uppercase tracking-widest text-white glow">
                            long-term memory
                        </div>
                        <div className="label text-[10px] mt-1">
                            {memories.length} stored fragments
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={wipeAll}
                            disabled={!memories.length}
                            data-testid="memory-wipe-all-btn"
                            className="heading text-[10px] uppercase tracking-widest px-3 py-1.5 border border-[#FF2A2A]/60 text-[#FF2A2A] hover:bg-[#FF2A2A]/10 disabled:opacity-30"
                        >
                            erase all
                        </button>
                        <button
                            onClick={onClose}
                            data-testid="memory-close-btn"
                            className="text-[#888] hover:text-white p-1"
                            aria-label="close"
                        >
                            <X size={18} />
                        </button>
                    </div>
                </header>

                <div className="px-5 py-3 border-b border-white/10">
                    <input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="filter memories..."
                        className="w-full bg-transparent outline-none text-sm font-mono text-white placeholder:text-[#444] border-b border-white/10 focus:border-[#CCFF00]/60 pb-2"
                        data-testid="memory-search-input"
                    />
                </div>

                <div className="flex-1 overflow-y-auto althea-scroll px-5 py-3 space-y-2">
                    {loading && (
                        <div className="text-[11px] text-[#888] caret">
                            recalling
                        </div>
                    )}
                    {!loading && filtered.length === 0 && (
                        <div className="text-[12px] text-[#666]">
                            no memories match. althea will accrue more as
                            you converse.
                        </div>
                    )}
                    {filtered.map((m) => (
                        <article
                            key={m.id}
                            className="fade-up border border-white/10 hover:border-[#CCFF00]/40 p-3 flex items-start gap-3"
                            data-testid={`memory-item-${m.id}`}
                        >
                            <div className="flex-1 min-w-0">
                                <div className="label text-[9px] mb-1 flex items-center gap-2">
                                    <span className="text-[#CCFF00]">
                                        {m.source}
                                    </span>
                                    <span className="text-[#666]">
                                        {new Date(m.timestamp)
                                            .toISOString()
                                            .replace("T", " ")
                                            .slice(0, 19)}
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
                                <div className="text-[12px] text-white/90 whitespace-pre-wrap break-words">
                                    {m.content}
                                </div>
                                <div className="text-[9px] text-[#444] mt-1 font-mono">
                                    id: {m.id}
                                </div>
                            </div>
                            <button
                                onClick={() => removeOne(m.id)}
                                data-testid={`memory-delete-${m.id}`}
                                className="text-[#888] hover:text-[#FF2A2A] shrink-0 p-1"
                                aria-label="delete"
                            >
                                <Trash2 size={14} />
                            </button>
                        </article>
                    ))}
                </div>

                <footer className="px-5 py-3 border-t border-white/10 text-[10px] text-[#666]">
                    tip: in the terminal type{" "}
                    <span className="text-[#CCFF00]">/memory</span>,{" "}
                    <span className="text-[#CCFF00]">/remember &lt;text&gt;</span>,{" "}
                    <span className="text-[#CCFF00]">/forget &lt;id-prefix&gt;</span>,{" "}
                    <span className="text-[#CCFF00]">/clear-memory</span>
                </footer>
            </aside>
        </div>
    );
};

export default MemoryDrawer;
