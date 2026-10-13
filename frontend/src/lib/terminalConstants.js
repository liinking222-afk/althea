// ─── ALTHEA terminal constants ─────────────────────────────────────
// Extracted from ChatConsole.jsx (P2 refactor) to keep the main component lean.

// Static slash commands. Grown capability slugs are merged at runtime.
export const STATIC_SLASH = [
    "/help", "/clear", "/mode", "/memory", "/introspect", "/evolve", "/vectors",
    "/cycles", "/version", "/imagine", "/letter", "/notif", "/research", "/grow", "/diagnose",
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
    AUTOPILOT: "#FF2A88",
    RESEARCH: "#A29BFE",
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
    "ALTHEA // your private mind — commands\n" +
    "── talk ────────────────────────────────\n" +
    "just type            converse with your althea\n" +
    "/mode direct|hybrid  zero-LLM local cognition vs hybrid\n" +
    "/imagine <prompt>    generate an image\n" +
    "/letter <topic>      draft a letter / document\n" +
    "plot <expression>    render a chart\n" +
    "── mind ────────────────────────────────\n" +
    "/memory [query]      open your memory drawer\n" +
    "/introspect          live self-state readout\n" +
    "/research <topic>    spawn an autonomous research thread\n" +
    "/grow                synthesize a capability for a detected gap\n" +
    "/diagnose            self-diagnostics\n" +
    "── evolution engine AEE/2.0 ────────────\n" +
    "/evolve [vector]     self-upgrade now (vector forces target)\n" +
    "/vectors             live self-assessment of 8 growth vectors\n" +
    "/cycles · /version   upgrade timeline · current self-version\n" +
    "── people ──────────────────────────────\n" +
    "open a direct line from the right panel — one shared althea joins you both;\n" +
    "mention @althea in that chat to call her, or use her terminal beside yours.\n" +
    "── misc ────────────────────────────────\n" +
    "/notif · /clear      notifications · clear screen";

export const getMessageTag = (content) => {
    const m = (content || "").match(/^\s*\[([A-Z][A-Z0-9\-_/]*)/);
    return m ? m[1] : null;
};
