// GraphExplorerPanel — click a concept node → see its neighbors, evidence
// trail and the research threads that grew it. Shared by NeuralCore (3D
// lattice) and ResearchScreen (2D radial graph).
import React, { useEffect, useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { X, GitBranch, Loader2, ExternalLink, FileSearch } from "lucide-react";

const V = "#A29BFE";

export const GraphExplorerPanel = ({ nodeId, onSelect, onClose }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [err, setErr] = useState(null);

    useEffect(() => {
        let live = true;
        setLoading(true);
        setErr(null);
        axios
            .get(`${API}/research/node/${nodeId}`)
            .then((r) => live && setData(r.data))
            .catch(() => live && setErr("node lookup failed"))
            .finally(() => live && setLoading(false));
        return () => {
            live = false;
        };
    }, [nodeId]);

    const n = data?.node;
    return (
        <div
            className="h-full flex flex-col border bg-black/85 backdrop-blur-md overflow-hidden"
            style={{ borderColor: "rgba(162,155,254,0.45)" }}
            data-testid="graph-explorer-panel"
        >
            <header className="flex items-center gap-2 px-3 py-2 border-b border-white/10 shrink-0">
                <GitBranch size={12} style={{ color: V }} />
                <span className="heading text-[9px] uppercase tracking-widest" style={{ color: V }}>
                    graph explorer
                </span>
                <button
                    onClick={onClose}
                    data-testid="graph-explorer-close"
                    className="ml-auto text-[#888] hover:text-white"
                >
                    <X size={13} />
                </button>
            </header>

            <div className="flex-1 min-h-0 overflow-y-auto althea-scroll p-3 space-y-3">
                {loading && (
                    <div className="flex items-center gap-2 text-[10px] font-mono text-[#888]">
                        <Loader2 size={11} className="animate-spin" /> resolving node…
                    </div>
                )}
                {err && <div className="text-[10px] font-mono text-[#FF2A2A]">{err}</div>}

                {n && (
                    <>
                        <div>
                            <div
                                className="heading text-sm uppercase tracking-wider text-white"
                                data-testid="graph-explorer-concept"
                            >
                                {n.concept}
                            </div>
                            <div className="flex gap-3 mt-1.5 text-[9px] font-mono text-[#888]">
                                <span>
                                    weight <span style={{ color: V }}>{Number(n.weight).toFixed(1)}</span>
                                </span>
                                <span>
                                    confidence{" "}
                                    <span className="text-[#CCFF00]">
                                        {Math.round((n.confidence || 0) * 100)}%
                                    </span>
                                </span>
                            </div>
                            <div className="h-1 bg-white/10 mt-1.5">
                                <div
                                    className="h-full"
                                    style={{
                                        width: `${Math.round((n.confidence || 0) * 100)}%`,
                                        background: `linear-gradient(90deg, ${V}, #CCFF00)`,
                                    }}
                                />
                            </div>
                        </div>

                        <div>
                            <div className="label text-[8px] uppercase tracking-widest text-[#888] mb-1.5">
                                neighbors · {data.neighbors.length} — click to expand
                            </div>
                            {data.neighbors.length === 0 && (
                                <div className="text-[9px] font-mono text-[#666]">
                                    no linked concepts yet
                                </div>
                            )}
                            <div className="flex flex-wrap gap-1">
                                {data.neighbors.map((nb) => (
                                    <button
                                        key={nb.node_id}
                                        onClick={() => onSelect(nb.node_id, nb.concept)}
                                        data-testid="graph-explorer-neighbor"
                                        className="text-[9px] font-mono px-1.5 py-0.5 border border-[#A29BFE]/40 text-[#A29BFE] hover:bg-[#A29BFE]/15 hover:border-[#A29BFE]"
                                        title={`link strength ${Number(nb.strength).toFixed(1)}`}
                                    >
                                        {nb.concept}
                                        <span className="text-[#666] ml-1">×{Number(nb.strength).toFixed(0)}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div>
                            <div className="label text-[8px] uppercase tracking-widest text-[#888] mb-1.5">
                                evidence · research queries that grew this node
                            </div>
                            {data.evidence.length === 0 && (
                                <div className="text-[9px] font-mono text-[#666]">no evidence recorded</div>
                            )}
                            <div className="space-y-1">
                                {data.evidence.map((q, i) => (
                                    <div
                                        key={i}
                                        className="text-[9px] font-mono text-white/70 flex gap-1.5"
                                        data-testid="graph-explorer-evidence"
                                    >
                                        <FileSearch size={9} className="shrink-0 mt-0.5" style={{ color: V }} />
                                        <span>"{q}"</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {data.threads.length > 0 && (
                            <div>
                                <div className="label text-[8px] uppercase tracking-widest text-[#888] mb-1.5">
                                    source threads
                                </div>
                                <div className="space-y-1.5">
                                    {data.threads.map((t) => (
                                        <div
                                            key={t.thread_id}
                                            className="border border-white/10 p-1.5"
                                            data-testid="graph-explorer-thread"
                                        >
                                            <div className="text-[9px] font-mono text-white/80 truncate">
                                                {t.query}
                                            </div>
                                            <div className="text-[8px] font-mono text-[#888] mt-0.5">
                                                conf {Math.round((t.confidence || 0) * 100)}% ·{" "}
                                                {(t.cross_refs || []).length} corroborated
                                            </div>
                                            {(t.citations || []).slice(0, 3).map((u, i) => (
                                                <a
                                                    key={i}
                                                    href={u}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="block text-[8px] font-mono text-[#9fb] hover:text-[#CCFF00] truncate"
                                                >
                                                    <ExternalLink size={8} className="inline mr-1" />
                                                    {u}
                                                </a>
                                            ))}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default GraphExplorerPanel;
