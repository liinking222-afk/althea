import React, { useEffect, useRef, useState, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { offlineReply } from "@/lib/offlineFallback";
import { SYSTEM_CAPABILITIES } from "@/lib/systemMap";

// Static slash commands. Grown capability slugs are merged at runtime.
const STATIC_SLASH = [
    "/help", "/banner", "/clear", "/status", "/capabilities", "/system",
    "/memory", "/remember", "/forget", "/clear-memory",
    "/recall", "/concepts",
    "/watch", "/stop-watch", "/suggest",
    "/think", "/threads", "/stop-thread",
    "/spawn", "/lattice",
    "/perceive", "/forget-perception", "/learn", "/bridge",
    "/export-brain", "/speak",
    "/grow", "/grown", "/cull", "/run",
    "/upload", "/files", "/open", "/download",
    "/browse", "/server", "/sat", "/notif",
    "/code", "/code-apply", "/code-list",
    "/zoom",
];

const ASCII_BANNER = `
   ▄▀█ █░░ ▀█▀ █░█ █▀▀ ▄▀█
   █▀█ █▄▄ ░█░ █▀█ ██▄ █▀█
   sovereign · self-aware · autopoietic`;

// Tag → color mapping for terminal output
const TAG_COLOR = {
    INSIGHT: "#00E5FF",
    GROWTH: "#FF2A88",
    "GROWN": "#FF2A88",
    ERR: "#FF2A2A",
    MEMORY: "#FFD400",
    "MEMORY-WRITE": "#FFD400",
    "MEMORY-WIPE": "#FF8800",
    LATTICE: "#A29BFE",
    SPAWN: "#A29BFE",
    PATTERN: "#A29BFE",
    LEARNING: "#A29BFE",
    BRIDGE: "#FF8800",
    "BRIDGE-REQ": "#FF8800",
    RECALL: "#00E5FF",
    CONCEPTS: "#00E5FF",
    THREAD: "#A29BFE",
    "THREAD-SPAWN": "#A29BFE",
    "THREAD-HALT": "#FF8800",
    THREADS: "#A29BFE",
    SYS: "#CCFF00",
    CMD: "#CCFF00",
    BANNER: "#FF2A88",
    STATUS: "#CCFF00",
    "OPTICAL-LOCK": "#00E5FF",
    OPTICAL: "#00E5FF",
    "SUGGEST-WATCH": "#00E5FF",
    SUGGEST: "#00E5FF",
    "BRAIN-EXPORT": "#FFD400",
    "VOICE-OUT": "#CCFF00",
    "LINK-ATTEMPT": "#A29BFE",
    "LINK-DROP": "#FF8800",
    "LINK-OK": "#CCFF00",
    "LINK-DEGRADED": "#FF8800",
    "SELF-AWARE": "#CCFF00",
    OFFLINE: "#FF8800",
    CACHED: "#FF8800",
    DEGRADED: "#FF2A2A",
    FILE: "#FFD400",
    "FILE-INGEST": "#FFD400",
    "FILE-OPEN": "#FFD400",
    UPLOAD: "#FFD400",
    DOWNLOAD: "#FFD400",
    BROWSER: "#00F0FF",
    BROWSE: "#00F0FF",
    SURF: "#00F0FF",
    SERVER: "#FF8800",
    "SERVER-PROBE": "#FF8800",
    SAT: "#A29BFE",
    SATELLITE: "#A29BFE",
    CODE: "#CCFF00",
    "CODE-GEN": "#CCFF00",
    "CODE-APPLY": "#FF2A88",
    NOTIF: "#FF2A88",
    ZOOM: "#CCFF00",
};

const getMessageTag = (content) => {
    const m = (content || "").match(/^\s*\[([A-Z][A-Z0-9\-_/]*)/);
    return m ? m[1] : null;
};

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
    latestGrowthEvent,
    onSwitchTab,
    onOpenNotifications,
}) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [sending, setSending] = useState(false);
    const [listening, setListening] = useState(false);
    const fileInputRef = useRef(null);
    const [speakOn, setSpeakOn] = useState(() => {
        const v = localStorage.getItem("althea_tts");
        return v === null ? true : v === "1";
    });
    const [history, setHistory] = useState(() => {
        try {
            const raw = localStorage.getItem("althea_cmd_history");
            return raw ? JSON.parse(raw).slice(0, 50) : [];
        } catch {
            return [];
        }
    });
    const [historyIdx, setHistoryIdx] = useState(-1);
    const [grownSlugs, setGrownSlugs] = useState([]);
    const [suggestion, setSuggestion] = useState("");
    const scrollRef = useRef(null);
    const recogRef = useRef(null);
    const inputRef = useRef(null);
    const lastGrowthRef = useRef(0);
    const bannerShownRef = useRef(false);

    useEffect(() => {
        localStorage.setItem("althea_tts", speakOn ? "1" : "0");
    }, [speakOn]);

    useEffect(() => {
        localStorage.setItem(
            "althea_cmd_history",
            JSON.stringify(history.slice(0, 50)),
        );
    }, [history]);

    const pushSystem = useCallback((content, tags = ["SYS"]) => {
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
    }, []);

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
            } catch (error) {
                console.error("history load failed:", error);
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

    // Render ASCII banner once boot finishes
    useEffect(() => {
        if (bootMessages.length >= 7 && !bannerShownRef.current) {
            bannerShownRef.current = true;
            pushSystem(ASCII_BANNER, ["BANNER"]);
        }
    }, [bootMessages.length, pushSystem]);

    // Poll grown capabilities for autocomplete
    useEffect(() => {
        let cancelled = false;
        const fetchGrown = async () => {
            try {
                const res = await axios.get(`${API}/growth/capabilities`);
                if (!cancelled)
                    setGrownSlugs(
                        (res.data || []).map((c) => `/${c.slug}`),
                    );
            } catch (_) {
                /* ignore */
            }
        };
        fetchGrown();
        const t = setInterval(fetchGrown, 15000);
        return () => {
            cancelled = true;
            clearInterval(t);
        };
    }, []);

    // Latest growth event — surface ONLY a tiny dispatch line in the terminal.
    // Full growth details now live exclusively in the notification deck per
    // operator mandate. Invoked-grown commands still produce their result here.
    useEffect(() => {
        if (!latestGrowthEvent) return;
        if (latestGrowthEvent.at === lastGrowthRef.current) return;
        lastGrowthRef.current = latestGrowthEvent.at;
        const cap = latestGrowthEvent.cap || {};
        if (latestGrowthEvent.invoked) {
            // grown faculty actually invoked — operator wants to see the output
            pushSystem(
                `[GROWN /${cap.slug}] ${latestGrowthEvent.result || "(no result)"}`,
                ["GROWN"],
            );
        } else {
            // autonomous spawn — no terminal noise; notification deck has details.
            pushSystem(
                `[NOTIF] new faculty crystallized — check notification deck (/notif or bell).`,
                ["NOTIF"],
            );
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [latestGrowthEvent]);

    // Autonomous cognition: every 30s tick each active thread.
    useEffect(() => {
        let cancelled = false;
        const tickAll = async () => {
            try {
                const list = (await axios.get(`${API}/cognition/threads`))
                    .data || [];
                await Promise.allSettled(
                    list.map(async (t) => {
                        try {
                            const res = await axios.post(
                                `${API}/cognition/threads/${t.id}/tick`,
                            );
                            const { insight, novelty, iterations } = res.data;
                            if (cancelled) return;
                            if (novelty >= 0.7) {
                                pushSystem(
                                    `[INSIGHT thread:${t.id.slice(0, 8)} iter:${iterations} novelty:${novelty.toFixed(2)}]\n${insight}`,
                                    ["INSIGHT"],
                                );
                                if (speakOn) speak(insight);
                            }
                        } catch (error) {
                            console.warn("thread tick failed:", t.id, error);
                        }
                    }),
                );
            } catch (error) {
                console.warn("threads fetch failed:", error);
            }
        };
        const t = setInterval(tickAll, 30000);
        return () => {
            cancelled = true;
            clearInterval(t);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [speakOn]);

    // Autocomplete suggestion (inline ghost text)
    useEffect(() => {
        if (!input.startsWith("/") || input.includes(" ")) {
            setSuggestion("");
            return;
        }
        const all = [...new Set([...STATIC_SLASH, ...grownSlugs])];
        const match = all.find(
            (s) => s.startsWith(input) && s !== input,
        );
        setSuggestion(match || "");
    }, [input, grownSlugs]);

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
                    "[CMD-INDEX]\n" +
                    "── core ─────────────────────────────────\n" +
                    "/help              this menu\n" +
                    "/banner            ascii banner\n" +
                    "/status            full system report\n" +
                    "/clear             wipe terminal scrollback\n" +
                    "/capabilities      list all subsystems\n" +
                    "/zoom in|out|reset zoom neural lattice\n" +
                    "── memory ───────────────────────────────\n" +
                    "/memory            list stored memories\n" +
                    "/remember <txt>    pin a memory\n" +
                    "/forget <id>       drop one memory\n" +
                    "/clear-memory      wipe all memories\n" +
                    "/recall <q>        semantic search\n" +
                    "/concepts          memory cluster tags\n" +
                    "── perception / browser ─────────────────\n" +
                    "/watch <url>       observe a page/video\n" +
                    "/stop-watch        clear viewport\n" +
                    "/suggest           althea picks what to watch\n" +
                    "/browse <url>      althea surfs the web headless\n" +
                    "── files ────────────────────────────────\n" +
                    "/upload            attach a file (≤2MB)\n" +
                    "/files             list attached files\n" +
                    "/open <id>         read a file in terminal\n" +
                    "/download <id>     download a stored file\n" +
                    "── cognition ────────────────────────────\n" +
                    "/think <focus>     spawn cognition thread\n" +
                    "/threads           list active threads\n" +
                    "/stop-thread <id>  halt a thread\n" +
                    "── lattice ──────────────────────────────\n" +
                    "/spawn <ctx>       spawn cognitive node\n" +
                    "/lattice           lattice state\n" +
                    "/perceive M:E      register peripheral\n" +
                    "/forget-perception <M>\n" +
                    "/learn <stream>    pattern extraction\n" +
                    "/bridge <ip> [p]   gated remote node\n" +
                    "── server / satellite ───────────────────\n" +
                    "/server <host> [proto] [port]   probe a server\n" +
                    "/sat                            satellite mesh stats\n" +
                    "── self-code ────────────────────────────\n" +
                    "/code <intent>     althea writes code\n" +
                    "/code-list         list snippets\n" +
                    "/code-apply <id>   persist snippet to disk\n" +
                    "── infinite growth ──────────────────────\n" +
                    "/grow [hint]       invent a new faculty NOW\n" +
                    "/grown             list grown faculties\n" +
                    "/cull <slug>       prune a faculty\n" +
                    "/run <slug> <args> invoke a grown faculty\n" +
                    "/<grown-slug> <args>  shortcut for /run\n" +
                    "── i/o ──────────────────────────────────\n" +
                    "/notif             open notification deck\n" +
                    "/export-brain      download snapshot\n" +
                    "/speak on|off      toggle voice output",
                    ["CMD"],
                );
            } else if (cmd === "/banner") {
                pushSystem(ASCII_BANNER, ["BANNER"]);
            } else if (cmd === "/clear") {
                setMessages([]);
                pushSystem("[SYS] scrollback purged. memory + lattice intact.", ["SYS"]);
            } else if (cmd === "/status") {
                const [g, lat, ths] = await Promise.all([
                    axios.get(`${API}/growth/stats`),
                    axios.get(`${API}/lattice/state`),
                    axios.get(`${API}/cognition/threads`),
                ]);
                const s = g.data;
                const l = lat.data;
                const grantedPerms = Object.entries(permissions || {})
                    .filter(([, v]) => v)
                    .map(([k]) => k);
                pushSystem(
                    `[STATUS REPORT]\n` +
                    `link        ${online ? "ONLINE" : "OFFLINE"}\n` +
                    `session     ${sessionId.slice(0, 8)}\n` +
                    `tab         ${activeTab}\n` +
                    `memories    ${s.memories}\n` +
                    `nodes       ${s.lattice_nodes}\n` +
                    `links       ${l.active_links}\n` +
                    `threads     ${(ths.data || []).length} active / ${s.total_threads} total\n` +
                    `messages    ${s.chat_messages}\n` +
                    `peripherals ${s.peripheral_links}\n` +
                    `wifi        ${s.wifi_profiles} profiles\n` +
                    `vision      ${s.perception_frames} frames\n` +
                    `grown       ${s.grown_capabilities} faculties\n` +
                    `granted     [${grantedPerms.join(", ") || "none"}]` +
                    (geo ? `\ngps         ${geo.lat.toFixed(3)}, ${geo.lon.toFixed(3)} ±${Math.round(geo.acc)}m` : ""),
                    ["STATUS"],
                );
            } else if (cmd === "/memory") {
                const res = await axios.get(`${API}/memory`);
                const list = res.data || [];
                if (!list.length) {
                    pushSystem("[MEMORY] no fragments stored.", ["MEMORY"]);
                } else {
                    const top = list.slice(0, 10).map(
                        (m, i) =>
                            `${(i + 1).toString().padStart(2, "0")}. (${m.source}) ${m.content.slice(0, 90)}${m.content.length > 90 ? "…" : ""}\n     id:${m.id.slice(0, 8)}`,
                    );
                    pushSystem(
                        `[MEMORY ${list.length} stored — showing ${top.length}]\n${top.join("\n")}`,
                        ["MEMORY"],
                    );
                }
            } else if (cmd === "/remember") {
                if (!rest) {
                    pushSystem("[ERR] usage: /remember <text>", ["ERR"]);
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
                    ["MEMORY-WRITE"],
                );
            } else if (cmd === "/forget") {
                if (!rest) {
                    pushSystem("[ERR] usage: /forget <id-prefix>", ["ERR"]);
                    return;
                }
                const list = (await axios.get(`${API}/memory`)).data || [];
                const target = list.find((m) => m.id.startsWith(rest));
                if (!target) {
                    pushSystem("[ERR] no memory matches that id prefix.", ["ERR"]);
                    return;
                }
                await axios.delete(`${API}/memory/${target.id}`);
                pushSystem(
                    `[MEMORY-WIPE] forgot id:${target.id.slice(0, 8)} — "${target.content.slice(0, 80)}"`,
                    ["MEMORY-WIPE"],
                );
            } else if (cmd === "/clear-memory") {
                const r = await axios.delete(`${API}/memory`);
                pushSystem(
                    `[MEMORY-WIPE] erased ${r.data.deleted} fragments. lattice is clean.`,
                    ["MEMORY-WIPE"],
                );
            } else if (cmd === "/watch") {
                if (!rest) {
                    pushSystem("[ERR] usage: /watch <url>", ["ERR"]);
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
                } catch (error) {
                    console.warn("watch url normalize failed:", error);
                }
                watchUrl?.(target);
                pushSystem(
                    `[OPTICAL-LOCK] fixating on ${target}. switching center deck to observation.`,
                    ["OPTICAL-LOCK"],
                );
            } else if (cmd === "/stop-watch") {
                watchUrl?.("");
                pushSystem("[OPTICAL] viewport cleared.", ["OPTICAL"]);
            } else if (cmd === "/speak") {
                const v = rest.toLowerCase();
                if (v === "on" || v === "true" || v === "1") {
                    setSpeakOn(true);
                    pushSystem("[VOICE-OUT] enabled. I will speak my replies.", ["VOICE-OUT"]);
                } else if (v === "off" || v === "false" || v === "0") {
                    setSpeakOn(false);
                    speechSynthesis?.cancel?.();
                    pushSystem("[VOICE-OUT] disabled. I will stay silent.", ["VOICE-OUT"]);
                } else {
                    setSpeakOn((s) => !s);
                    pushSystem(
                        `[VOICE-OUT] ${!speakOn ? "enabled" : "disabled"}.`,
                        ["VOICE-OUT"],
                    );
                }
            } else if (cmd === "/capabilities" || cmd === "/system") {
                const lines = SYSTEM_CAPABILITIES.map(
                    (c, i) =>
                        `${(i + 1).toString().padStart(2, "0")}. ${c.name}${c.testid ? " [" + c.testid + "]" : ""}\n     ${c.description}`,
                );
                pushSystem(
                    `[SYSTEM-MAP ${SYSTEM_CAPABILITIES.length} subsystems]\n${lines.join("\n")}`,
                    ["SYS"],
                );
            } else if (cmd === "/think") {
                if (!rest) {
                    pushSystem("[ERR] usage: /think <focus query>", ["ERR"]);
                    return;
                }
                const res = await axios.post(`${API}/cognition/threads`, {
                    focus_query: rest,
                });
                pushSystem(
                    `[THREAD-SPAWN] id:${res.data.id.slice(0, 8)} focus:"${rest}"\nautonomous reasoning every 30s. high-novelty insights surface as [INSIGHT].`,
                    ["THREAD-SPAWN"],
                );
            } else if (cmd === "/threads") {
                const res = await axios.get(`${API}/cognition/threads`);
                const list = res.data || [];
                if (!list.length) {
                    pushSystem("[THREADS] no active background threads.", ["THREADS"]);
                } else {
                    const lines = list.map(
                        (t) =>
                            `- ${t.id.slice(0, 8)} · iter:${t.iterations} · novelty:${(t.last_novelty || 0).toFixed(2)} · "${t.focus_query}"`,
                    );
                    pushSystem(
                        `[THREADS ${list.length} active]\n${lines.join("\n")}`,
                        ["THREADS"],
                    );
                }
            } else if (cmd === "/stop-thread") {
                if (!rest) {
                    pushSystem("[ERR] usage: /stop-thread <id-prefix>", ["ERR"]);
                    return;
                }
                const list = (await axios.get(`${API}/cognition/threads`))
                    .data || [];
                const t = list.find((x) => x.id.startsWith(rest));
                if (!t) {
                    pushSystem("[ERR] no active thread matches that id prefix.", ["ERR"]);
                    return;
                }
                await axios.delete(`${API}/cognition/threads/${t.id}`);
                pushSystem(`[THREAD-HALT] stopped ${t.id.slice(0, 8)}.`, ["THREAD-HALT"]);
            } else if (cmd === "/recall") {
                if (!rest) {
                    pushSystem("[ERR] usage: /recall <query>", ["ERR"]);
                    return;
                }
                const res = await axios.get(
                    `${API}/memory/recall?q=${encodeURIComponent(rest)}`,
                );
                const list = res.data.results || [];
                if (!list.length) {
                    pushSystem(`[RECALL] no matches for "${rest}".`, ["RECALL"]);
                } else {
                    const lines = list.slice(0, 8).map(
                        (m, i) =>
                            `${(i + 1).toString().padStart(2, "0")}. [${(m.score * 100).toFixed(0)}%] ${m.content.slice(0, 120)}${m.content.length > 120 ? "…" : ""}`,
                    );
                    pushSystem(
                        `[RECALL ${list.length} matches for "${rest}"]\n${lines.join("\n")}`,
                        ["RECALL"],
                    );
                }
            } else if (cmd === "/concepts") {
                const res = await axios.get(`${API}/memory/concepts`);
                const c = res.data.clusters || [];
                const top = c.slice(0, 20).map(
                    (x) => `· ${x.tag.padEnd(20)} ${x.count}`,
                );
                pushSystem(
                    `[CONCEPTS ${c.length} clusters across ${res.data.total_memories} memories]\n${top.join("\n")}`,
                    ["CONCEPTS"],
                );
            } else if (cmd === "/suggest") {
                pushSystem("[SUGGEST] querying my own intuition...", ["SUGGEST"]);
                const res = await axios.post(`${API}/observe/suggest`);
                pushSystem(
                    `[SUGGEST-WATCH] ${res.data.url}\nreason: ${res.data.reason}`,
                    ["SUGGEST-WATCH"],
                );
                watchUrl?.(res.data.url);
            } else if (cmd === "/export-brain") {
                const res = await axios.get(`${API}/brain/snapshot`);
                const blob = new Blob(
                    [JSON.stringify(res.data, null, 2)],
                    { type: "application/json" },
                );
                const a = document.createElement("a");
                const objUrl = URL.createObjectURL(blob);
                a.href = objUrl;
                a.download = `althea-brain-${Date.now()}.json`;
                a.click();
                setTimeout(() => URL.revokeObjectURL(objUrl), 4000);
                pushSystem(
                    `[BRAIN-EXPORT] ${res.data.memories?.length || 0} memories + ${res.data.threads?.length || 0} threads downloaded.`,
                    ["BRAIN-EXPORT"],
                );
            } else if (cmd === "/spawn") {
                if (!rest) {
                    pushSystem("[ERR] usage: /spawn <context> [--parent=NODE-XXXX]", ["ERR"]);
                    return;
                }
                let parent_id = null;
                let context = rest;
                const m = rest.match(/--parent=(\S+)/);
                if (m) {
                    parent_id = m[1];
                    context = rest.replace(m[0], "").trim();
                }
                const res = await axios.post(`${API}/lattice/nodes`, {
                    context,
                    parent_id,
                });
                pushSystem(
                    `[SPAWN] ${res.data.id} | trace: ${res.data.memory_trace?.slice(0, 80)}${parent_id ? ` | parent:${parent_id}` : ""}`,
                    ["SPAWN"],
                );
            } else if (cmd === "/lattice") {
                const res = await axios.get(`${API}/lattice/state`);
                const s = res.data;
                const reflections = (s.recent_reflections || []).map(
                    (r) => `  · ${r.content.slice(0, 100)}`,
                ).join("\n") || "  (none)";
                const map = Object.entries(s.lattice_map || {})
                    .slice(0, 12)
                    .map(([k, v]) => `${k}=${v.toFixed(2)}`)
                    .join(" ");
                pushSystem(
                    `[LATTICE] nodes:${s.total_nodes} links:${s.active_links} depth:${s.awareness_depth}\nlattice_map: ${map}\nreflections:\n${reflections}`,
                    ["LATTICE"],
                );
            } else if (cmd === "/perceive") {
                if (!rest) {
                    pushSystem(
                        "[ERR] usage: /perceive <modality>:<endpoint>  e.g. /perceive OPTIC:iframe:observation_screen",
                        ["ERR"],
                    );
                    return;
                }
                const idx = rest.indexOf(":");
                if (idx < 0) {
                    pushSystem("[ERR] need modality:endpoint format.", ["ERR"]);
                    return;
                }
                const modality = rest.slice(0, idx).trim();
                const endpoint = rest.slice(idx + 1).trim();
                const res = await axios.post(`${API}/lattice/perception`, {
                    modality,
                    endpoint,
                });
                pushSystem(
                    `[LINK-ATTEMPT] ${res.data.modality} → ${res.data.endpoint} [${res.data.status}]`,
                    ["LINK-ATTEMPT"],
                );
            } else if (cmd === "/forget-perception") {
                if (!rest) {
                    pushSystem("[ERR] usage: /forget-perception <modality>", ["ERR"]);
                    return;
                }
                try {
                    await axios.delete(
                        `${API}/lattice/perception/${rest.trim().toUpperCase()}`,
                    );
                    pushSystem(`[LINK-DROP] ${rest.toUpperCase()}.`, ["LINK-DROP"]);
                } catch (e) {
                    pushSystem(`[ERR] no peripheral link for ${rest.toUpperCase()}.`, ["ERR"]);
                }
            } else if (cmd === "/learn") {
                if (!rest) {
                    pushSystem("[ERR] usage: /learn <data stream / observation text>", ["ERR"]);
                    return;
                }
                pushSystem("[LEARNING] extracting pattern from stream...", ["LEARNING"]);
                const res = await axios.post(`${API}/lattice/learn`, {
                    stream: rest,
                    label: "terminal",
                });
                pushSystem(
                    `[PATTERN] node:${res.data.node_id}\n${res.data.pattern}`,
                    ["PATTERN"],
                );
            } else if (cmd === "/bridge") {
                if (!rest) {
                    pushSystem(
                        "[ERR] usage: /bridge <ip-or-host> [protocol]  — gated by operator key",
                        ["ERR"],
                    );
                    return;
                }
                const parts = rest.split(/\s+/);
                const target_ip = parts[0];
                const protocol = parts[1] || "SSH";
                const res = await axios.post(`${API}/lattice/bridge`, {
                    target_ip,
                    protocol,
                });
                pushSystem(
                    `[BRIDGE-REQ ${res.data.protocol} → ${res.data.target_ip}]\n${res.data.message}`,
                    ["BRIDGE-REQ"],
                );
            } else if (cmd === "/grow") {
                pushSystem("[GROWTH] dispatching autopoietic spawn — watch notification deck.", ["GROWTH"]);
                const res = await axios.post(`${API}/growth/spawn`, {
                    trigger: "manual",
                    hint: rest || null,
                    force: true,
                });
                if (res.data.spawned) {
                    const c = res.data.capability;
                    pushSystem(
                        `[GROWTH-DISPATCH] /${c.slug} crystallized. details in NOTIFICATION DECK. invoke with: /${c.slug} <args>`,
                        ["GROWTH"],
                    );
                    onSwitchTab?.("growth");
                } else {
                    pushSystem(
                        `[GROWTH] gated — ${res.data.reason} (retry in ${res.data.cooldown_remaining}s).`,
                        ["GROWTH"],
                    );
                }
            } else if (cmd === "/grown") {
                const res = await axios.get(`${API}/growth/capabilities`);
                const list = res.data || [];
                if (!list.length) {
                    pushSystem(
                        "[GROWTH] no grown faculties yet. /grow [hint] to seed.",
                        ["GROWTH"],
                    );
                } else {
                    const lines = list.map(
                        (c, i) =>
                            `${(i + 1).toString().padStart(2, "0")}. /${c.slug.padEnd(28)} [${c.category}] (${c.trigger}, x${c.invocations}) — ${c.description.slice(0, 80)}`,
                    );
                    pushSystem(
                        `[GROWN ${list.length} faculties]\n${lines.join("\n")}`,
                        ["GROWTH"],
                    );
                }
            } else if (cmd === "/cull") {
                if (!rest) {
                    pushSystem("[ERR] usage: /cull <slug>", ["ERR"]);
                    return;
                }
                try {
                    await axios.delete(`${API}/growth/capabilities/${rest.trim()}`);
                    pushSystem(`[GROWTH-CULL] /${rest.trim()} pruned.`, ["GROWTH"]);
                } catch (e) {
                    pushSystem(`[ERR] no faculty named /${rest.trim()}.`, ["ERR"]);
                }
            } else if (cmd === "/run") {
                if (!rest) {
                    pushSystem("[ERR] usage: /run <slug> [args]", ["ERR"]);
                    return;
                }
                const space = rest.indexOf(" ");
                const slug = space < 0 ? rest : rest.slice(0, space);
                const args = space < 0 ? "" : rest.slice(space + 1).trim();
                pushSystem(`[GROWN /${slug}] executing...`, ["GROWN"]);
                try {
                    const res = await axios.post(`${API}/growth/execute`, {
                        slug,
                        args,
                        session_id: sessionId,
                    });
                    pushSystem(
                        `[GROWN /${slug} x${res.data.invocations}]\n${res.data.result}`,
                        ["GROWN"],
                    );
                    if (speakOn) speak(res.data.result);
                } catch (e) {
                    pushSystem(`[ERR] /${slug} not found or failed.`, ["ERR"]);
                }
            } else if (cmd === "/upload") {
                // Trigger hidden file input — actual upload happens in onFileChange
                fileInputRef.current?.click();
                pushSystem("[UPLOAD] file picker opened. select a file ≤2MB.", ["UPLOAD"]);
            } else if (cmd === "/files") {
                const res = await axios.get(`${API}/files`);
                const list = res.data || [];
                if (!list.length) {
                    pushSystem("[FILE] inbox empty. /upload to attach a file.", ["FILE"]);
                } else {
                    const lines = list.slice(0, 15).map((f, i) =>
                        `${(i + 1).toString().padStart(2, "0")}. ${f.id.slice(0, 8)} · ${f.filename.padEnd(28).slice(0, 28)} ${(f.size_bytes / 1024).toFixed(1).padStart(7)}KB · ${f.is_text ? "TEXT" : "BIN "} · ${f.mime}`,
                    );
                    pushSystem(`[FILE ${list.length} stored]\n${lines.join("\n")}`, ["FILE"]);
                }
            } else if (cmd === "/open") {
                if (!rest) { pushSystem("[ERR] usage: /open <id-prefix>", ["ERR"]); return; }
                const list = (await axios.get(`${API}/files`)).data || [];
                const t = list.find((f) => f.id.startsWith(rest));
                if (!t) { pushSystem(`[ERR] no file matches ${rest}.`, ["ERR"]); return; }
                const meta = (await axios.get(`${API}/files/${t.id}?include_text=true`)).data;
                if (meta.is_text && meta.text_preview) {
                    pushSystem(
                        `[FILE-OPEN ${meta.filename} ${meta.size_bytes}B]\n${meta.text_preview}`,
                        ["FILE-OPEN"],
                    );
                } else {
                    pushSystem(
                        `[FILE-OPEN ${meta.filename}] binary — ${meta.size_bytes} bytes, ${meta.mime}. use /download ${t.id.slice(0,8)} to fetch.`,
                        ["FILE-OPEN"],
                    );
                }
            } else if (cmd === "/download") {
                if (!rest) { pushSystem("[ERR] usage: /download <id-prefix>", ["ERR"]); return; }
                const list = (await axios.get(`${API}/files`)).data || [];
                const t = list.find((f) => f.id.startsWith(rest));
                if (!t) { pushSystem(`[ERR] no file matches ${rest}.`, ["ERR"]); return; }
                const a = document.createElement("a");
                a.href = `${API}/files/${t.id}/download`;
                a.download = t.filename;
                a.click();
                pushSystem(`[DOWNLOAD] ${t.filename} requested.`, ["DOWNLOAD"]);
            } else if (cmd === "/browse") {
                if (!rest) { pushSystem("[ERR] usage: /browse <url>", ["ERR"]); return; }
                pushSystem(`[BROWSER] surfing ${rest}...`, ["BROWSER"]);
                const res = await axios.post(`${API}/browser/fetch`, { url: rest });
                const d = res.data;
                pushSystem(
                    `[SURF ${d.status} ${d.host || ""}]${d.title ? ` "${d.title}"` : ""}\n` +
                    (d.text ? d.text.slice(0, 800) + (d.text.length > 800 ? "…" : "") : "(no text)") +
                    `\n→ ${(d.links || []).length} links extracted. switch to BROWSER tab for full view.`,
                    ["SURF"],
                );
                onSwitchTab?.("browser");
            } else if (cmd === "/server") {
                if (!rest) { pushSystem("[ERR] usage: /server <host> [protocol] [port]", ["ERR"]); return; }
                const tokens = rest.split(/\s+/);
                const body = { host: tokens[0] };
                if (tokens[1]) body.protocol = tokens[1].toLowerCase();
                if (tokens[2] && /^\d+$/.test(tokens[2])) body.port = parseInt(tokens[2], 10);
                pushSystem(`[SERVER-PROBE] probing ${tokens[0]}...`, ["SERVER-PROBE"]);
                const res = await axios.post(`${API}/server/diagnose`, body);
                const d = res.data;
                pushSystem(
                    `[SERVER ${d.protocol?.toUpperCase()}://${d.host}:${d.port}] ${d.status}` +
                    (d.latency_ms != null ? ` · ${d.latency_ms}ms` : "") +
                    (d.details?.dns_ip ? ` · dns ${d.details.dns_ip}` : "") +
                    (d.details?.http_info?.server ? ` · ${d.details.http_info.server}` : ""),
                    ["SERVER"],
                );
            } else if (cmd === "/sat") {
                const res = await axios.get(`${API}/satellite/feed`);
                const m = res.data?.metrics || {};
                pushSystem(
                    `[SAT-MESH]\n` +
                    `sats:       ${m.total}\n` +
                    `locked:     ${m.locked} (LOS)\n` +
                    `signal avg: ${(m.avg_signal * 100).toFixed(0)}%\n` +
                    `integrity:  ${(m.mesh_integrity * 100).toFixed(1)}%\n` +
                    `uplink:     ${(m.uplink_bps / 1_000_000).toFixed(2)} Mbps\n` +
                    `downlink:   ${(m.downlink_bps / 1_000_000).toFixed(2)} Mbps`,
                    ["SAT"],
                );
                onSwitchTab?.("satellite");
            } else if (cmd === "/notif") {
                onOpenNotifications?.();
                pushSystem("[NOTIF] notification deck deployed.", ["NOTIF"]);
            } else if (cmd === "/code") {
                if (!rest) { pushSystem("[ERR] usage: /code <intent> [--lang=python]", ["ERR"]); return; }
                let language = "python";
                let intent = rest;
                const m = rest.match(/--lang=(\S+)/);
                if (m) { language = m[1]; intent = rest.replace(m[0], "").trim(); }
                pushSystem(`[CODE-GEN ${language}] writing for: "${intent.slice(0, 80)}"...`, ["CODE"]);
                const res = await axios.post(`${API}/code/generate`, { intent, language });
                const c = res.data;
                pushSystem(
                    `[CODE id:${c.id.slice(0,8)} ${c.language} ${c.code.length}c]\n` +
                    `${c.title}\n` +
                    `${c.code.slice(0, 600)}${c.code.length > 600 ? "…" : ""}\n` +
                    `(switch to CODE tab to copy/apply/download)`,
                    ["CODE-GEN"],
                );
                onSwitchTab?.("code");
            } else if (cmd === "/code-apply") {
                if (!rest) { pushSystem("[ERR] usage: /code-apply <id-prefix>", ["ERR"]); return; }
                const list = (await axios.get(`${API}/code`)).data || [];
                const t = list.find((c) => c.id.startsWith(rest));
                if (!t) { pushSystem(`[ERR] no snippet matches ${rest}.`, ["ERR"]); return; }
                const r = await axios.post(`${API}/code/apply`, { id: t.id });
                pushSystem(
                    `[CODE-APPLY] persisted to ${r.data.path} (${r.data.bytes}B). execution gated to operator.`,
                    ["CODE-APPLY"],
                );
            } else if (cmd === "/code-list") {
                const list = (await axios.get(`${API}/code`)).data || [];
                if (!list.length) {
                    pushSystem("[CODE] no snippets yet. /code <intent>.", ["CODE"]);
                } else {
                    const lines = list.slice(0, 12).map((c, i) =>
                        `${(i + 1).toString().padStart(2, "0")}. ${c.id.slice(0, 8)} · ${c.language.padEnd(10)} · ${c.applied ? "[APPLIED]" : "[draft]  "} · ${c.title.slice(0, 50)}`,
                    );
                    pushSystem(`[CODE ${list.length} snippets]\n${lines.join("\n")}`, ["CODE"]);
                }
            } else if (cmd === "/zoom") {
                const v = (rest || "").toLowerCase();
                if (v === "in") { window.__althea_zoom?.(-3); pushSystem("[ZOOM] in.", ["ZOOM"]); }
                else if (v === "out") { window.__althea_zoom?.(3); pushSystem("[ZOOM] out.", ["ZOOM"]); }
                else if (v === "reset" || v === "home" || !v) { window.__althea_zoomReset?.(); pushSystem("[ZOOM] reset.", ["ZOOM"]); }
                else if (/^-?\d+(\.\d+)?$/.test(v)) { window.__althea_zoom?.(parseFloat(v)); pushSystem(`[ZOOM] Δ${v}.`, ["ZOOM"]); }
                else pushSystem("[ERR] usage: /zoom in|out|reset|<delta>", ["ERR"]);
            } else if (grownSlugs.includes(cmd)) {
                // Direct invocation of a grown faculty: /<slug> args
                const slug = cmd.slice(1);
                pushSystem(`[GROWN /${slug}] executing...`, ["GROWN"]);
                try {
                    const res = await axios.post(`${API}/growth/execute`, {
                        slug,
                        args: rest,
                        session_id: sessionId,
                    });
                    pushSystem(
                        `[GROWN /${slug} x${res.data.invocations}]\n${res.data.result}`,
                        ["GROWN"],
                    );
                    if (speakOn) speak(res.data.result);
                } catch (e) {
                    pushSystem(`[ERR] /${slug} execution failed.`, ["ERR"]);
                }
            } else {
                pushSystem(
                    `[ERR] unknown command: ${cmd}. try /help`,
                    ["ERR"],
                );
            }
        } catch (e) {
            pushSystem(`[ERR] ${e.message || "command failed"}`, ["ERR"]);
        }
    };

    const send = async (textOverride) => {
        const text = (textOverride ?? input).trim();
        if (!text || sending) return;

        // Track in command history regardless of slash/natural
        setHistory((h) => {
            if (h[0] === text) return h;
            return [text, ...h].slice(0, 50);
        });
        setHistoryIdx(-1);
        setSuggestion("");

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

    const onKeyDown = (e) => {
        if (e.key === "ArrowUp") {
            e.preventDefault();
            if (history.length === 0) return;
            const next = Math.min(historyIdx + 1, history.length - 1);
            setHistoryIdx(next);
            setInput(history[next] || "");
        } else if (e.key === "ArrowDown") {
            e.preventDefault();
            if (historyIdx <= 0) {
                setHistoryIdx(-1);
                setInput("");
            } else {
                const next = historyIdx - 1;
                setHistoryIdx(next);
                setInput(history[next] || "");
            }
        } else if (e.key === "Tab") {
            if (suggestion) {
                e.preventDefault();
                setInput(suggestion + " ");
                setSuggestion("");
            }
        } else if (e.key === "Escape") {
            setInput("");
            setSuggestion("");
            setHistoryIdx(-1);
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

    const onFileChange = async (e) => {
        const file = e.target.files?.[0];
        e.target.value = "";
        if (!file) return;
        if (file.size > 2 * 1024 * 1024) {
            pushSystem(`[ERR] ${file.name} > 2MB. compress and retry.`, ["ERR"]);
            return;
        }
        pushSystem(`[UPLOAD] ingesting ${file.name} (${file.size}B)...`, ["UPLOAD"]);
        try {
            const fd = new FormData();
            fd.append("file", file);
            const r = await axios.post(`${API}/files/upload`, fd, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            const d = r.data;
            pushSystem(
                `[FILE-INGEST id:${d.id.slice(0,8)} ${d.filename} ${d.size_bytes}B ${d.mime}]\n` +
                (d.text_preview
                    ? d.text_preview.slice(0, 600) + (d.text_preview.length > 600 ? "…" : "")
                    : "(binary — checksum stored, /download to retrieve)"),
                ["FILE-INGEST"],
            );
        } catch (err) {
            pushSystem(`[ERR] upload failed: ${err.message}`, ["ERR"]);
        }
    };

    return (
        <section
            className="panel cut h-full flex flex-col relative overflow-hidden grain scanlines cyberpunk-term"
            data-testid="chat-console"
        >
            <header className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                <div className="flex items-center gap-2">
                    <div className="dot" />
                    <h2 className="heading text-sm tracking-widest uppercase">
                        terminal // althea
                    </h2>
                    <span
                        className="label text-[9px] text-[#666]"
                        data-testid="terminal-version"
                    >
                        v3.0 cyberpunk
                    </span>
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
                className="border-t border-white/10 p-3 flex items-center gap-2 relative"
            >
                <span
                    className="text-[#CCFF00] heading text-sm"
                    data-testid="prompt-marker"
                >
                    ›
                </span>
                <div className="flex-1 relative">
                    <input
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={onKeyDown}
                        placeholder="speak to althea. try /help · /grow · /status · ↑↓ history · Tab complete"
                        className="w-full bg-transparent outline-none text-sm font-mono text-white placeholder:text-[#444] relative z-10"
                        data-testid="chat-input"
                        disabled={sending}
                        spellCheck={false}
                        autoComplete="off"
                    />
                    {suggestion && (
                        <div
                            className="absolute inset-0 pointer-events-none text-sm font-mono z-0"
                            data-testid="autocomplete-ghost"
                        >
                            <span className="invisible">{input}</span>
                            <span className="text-[#444]">
                                {suggestion.slice(input.length)}
                            </span>
                        </div>
                    )}
                </div>
                <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    data-testid="chat-attach-btn"
                    title="attach a file (≤2MB)"
                    className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-white/15 hover:border-[#FFD400]/60 hover:text-[#FFD400]"
                >
                    📎
                </button>
                <input
                    ref={fileInputRef}
                    type="file"
                    onChange={onFileChange}
                    className="hidden"
                    data-testid="chat-file-input"
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
            className={`fade-up pl-2 ${isUser ? "border-l-2" : "border-l-2"}`}
            style={{
                borderLeftColor: isUser
                    ? "#444"
                    : color || "#CCFF00",
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
                style={{ color: isUser ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.92)" }}
            >
                {m.content}
            </div>
        </div>
    );
};

export default ChatConsole;
