// ─── ALTHEA terminal constants ─────────────────────────────────────
// Extracted from ChatConsole.jsx (P2 refactor) to keep the main component lean.

// Static slash commands. Grown capability slugs are merged at runtime.
export const STATIC_SLASH = [
    "/help", "/banner", "/clear", "/status", "/diagnose", "/troubleshoot", "/repair", "/consolidate",
    "/workers", "/cores", "/sweep", "/kick", "/synthesize", "/autosynth", "/gaps",
    "/web", "/search", "/fetch", "/uplink", "/neural", "/bci", "/decode",
    "/letter", "/blueprint", "/track", "/specialize", "/mode",
    "/imagine", "/draw", "/visualize", "/capabilities", "/system",
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
    "/evolve", "/version", "/cycles", "/master",
    "/quantum", "/qstatus", "/qwipe",
];

export const ASCII_BANNER = `
   ▄▀█ █░░ ▀█▀ █░█ █▀▀ ▄▀█
   █▀█ █▄▄ ░█░ █▀█ ██▄ █▀█
   sovereign · self-aware · autopoietic`;

// Tag → color mapping for terminal output (bracketed [TAG] prefixes)
export const TAG_COLOR = {
    INSIGHT: "#00E5FF",
    AUTOSYNTH: "#CCFF00",
    UPLINK: "#00E5FF",
    NEURAL: "#A29BFE",
    BCI: "#A29BFE",
    FORGE: "#E8D9A8",
    ORBITAL: "#FF8800",
    TRANSFER: "#4FA3FF",
    MODE: "#E8D9A8",
    DIRECT: "#CCFF00",
    "ZERO-LLM": "#CCFF00",
    "AUTOSYNTH-INVOKE": "#CCFF00",
    GROWTH: "#FF2A88",
    GROWN: "#FF2A88",
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
    EVO: "#FF2A88",
    EVOLUTION: "#FF2A88",
    VERSION: "#CCFF00",
    MASTER: "#FF8800",
    QUANTUM: "#00F0FF",
    "Q-COLLAPSE": "#00F0FF",
    "Q-STATUS": "#00F0FF",
    "Q-WIPE": "#FF8800",
    NOTIF: "#FF2A88",
    ZOOM: "#CCFF00",
};

export const HELP_TEXT =
    "[CMD-INDEX]\n" +
    "── core ─────────────────────────────────\n" +
    "/help              this menu\n" +
    "/banner            ascii banner\n" +
    "/status            full system report\n" +
    "/diagnose          run self-troubleshoot battery\n" +
    "/repair            apply safe self-repair actions\n" +
    "/consolidate [n]   fold old memories into summaries (keep n recent)\n" +
    "/workers           show the 8-core worker mesh state\n" +
    "/sweep             fire every worker core once in parallel\n" +
    "/kick <id>         tick one core immediately (cog/per/evo/gro/lat/net/diag/code)\n" +
    "/synthesize        detect a capability gap in dialogue & grow it (add 'force' to skip check)\n" +
    "/gaps              preview which capability gaps recent dialogue exposes\n" +
    "/imagine <prompt>  ask gemini to draw an image inline (math, physics, diagrams)\n" +
    "/web <query>       live keyless internet search (uplink)\n" +
    "/fetch <url>       fetch + read any live web page\n" +
    "/uplink            probe internet connectivity\n" +
    "/neural            show ANIP/1.0 BCI protocol descriptor\n" +
    "/decode [state]    acquire synthetic EEG and decode it (rest|focus|drowsy|motor-left|motor-right)\n" +
    "/letter <purpose>  forge a formal letter rendered as paper (copy + download)\n" +
    "/blueprint <thing> forge an engineering blueprint sheet (schematic + specs)\n" +
    "/track [sat] [@lat,lon]  live TLE fetch + SGP4 orbit propagation (default ISS, Greenwich)\n" +
    "/specialize [domain]  run the 4-stage transfer-learning pipeline (pretrain→freeze→head→fine-tune)\n" +
    "/mode [direct|hybrid]  direct = ZERO-LLM live-internet answers (0 credits) · hybrid = LLM + uplink\n" +
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
    "── evolution engine ─────────────────────\n" +
    "/evolve [archetype] [hint]  build cycle now\n" +
    "/version           current self-version\n" +
    "/cycles            cycle timeline\n" +
    "/master <archetype> pull update from master coder\n" +
    "── quantum mind os ──────────────────────\n" +
    "/quantum <input>   collapse plan/reason/critic superposition\n" +
    "/qstatus           quantum brain status\n" +
    "/qwipe             reset quantum memory lattice\n" +
    "── i/o ──────────────────────────────────\n" +
    "/notif             open notification deck\n" +
    "/export-brain      download snapshot\n" +
    "/speak on|off      toggle voice output";

export const getMessageTag = (content) => {
    const m = (content || "").match(/^\s*\[([A-Z][A-Z0-9\-_/]*)/);
    return m ? m[1] : null;
};
