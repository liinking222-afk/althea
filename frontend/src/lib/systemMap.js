// Single source of truth for what Althea knows about herself.
// Imported by App.js on boot and POSTed to /api/system-map so the capability
// list lands in Althea's long-term memory and is automatically injected into
// every /api/chat system prompt.

export const SYSTEM_CAPABILITIES = [
    {
        name: "TopBar",
        testid: "althea-topbar",
        description:
            "Header with integrity/coherence/link metrics and the 'PURGE SESSION' button which wipes the current chat session.",
    },
    {
        name: "PurgeSessionButton",
        testid: "althea-reset-session-btn",
        description:
            "Erases the current chat history. Does NOT touch long-term memory.",
    },
    {
        name: "ChatTerminal",
        testid: "chat-console",
        description:
            "The left console where the operator types. Accepts natural language and slash commands.",
    },
    {
        name: "ChatInput",
        testid: "chat-input",
        description: "Text input where the operator addresses Althea.",
    },
    {
        name: "ChatSendButton",
        testid: "chat-send-btn",
        description: "Transmits the operator's message to Althea.",
    },
    {
        name: "VoiceInputButton",
        testid: "voice-input-btn",
        description:
            "Toggles browser SpeechRecognition. When pressed Althea listens.",
    },
    {
        name: "VoiceOutputToggle",
        testid: "voice-output-toggle",
        description:
            "When ON, Althea speaks her replies aloud via SpeechSynthesis.",
    },
    {
        name: "OpenMemoryButton",
        testid: "open-memory-btn",
        description: "Opens the long-term memory drawer.",
    },
    {
        name: "MemoryDrawer",
        testid: "memory-drawer",
        description:
            "Searchable list of every persistent memory. Each row has its own delete button. An 'ERASE ALL' button wipes everything.",
    },
    {
        name: "CenterDeck",
        testid: "center-deck",
        description:
            "The center panel. Holds two tabs: 'NEURAL' (live 3D lattice) and 'OBSERVE' (URL/video iframe).",
    },
    {
        name: "CenterTabNeural",
        testid: "center-tab-neural",
        description: "Switches the center deck to the neural lattice view.",
    },
    {
        name: "CenterTabObserve",
        testid: "center-tab-observe",
        description: "Switches the center deck to the observation viewport.",
    },
    {
        name: "NeuralCore",
        testid: "neural-core",
        description:
            "Live 3D neural network visualization, 30 nodes across 4 layers. Drag to rotate.",
    },
    {
        name: "ObservationScreen",
        testid: "observation-screen",
        description:
            "An iframe-based viewport. Althea fixates on whatever URL is loaded here. Auto-converts YouTube watch links to embeds. Every URL change is logged to memory and Althea generates an interpretation.",
    },
    {
        name: "ObservationUrlInput",
        testid: "observation-url-input",
        description: "Field for the operator to enter a URL or video link.",
    },
    {
        name: "ObservationLoadButton",
        testid: "observation-load-btn",
        description: "Loads the URL into the observation iframe.",
    },
    {
        name: "PermissionsPanel",
        testid: "permissions-panel",
        description:
            "Six toggles: camera, microphone, geolocation, bluetooth, web USB, notifications. Each invokes a real browser permission prompt.",
    },
    {
        name: "PublicGPSMap",
        testid: "map-container",
        description:
            "Leaflet+OpenStreetMap dark world map. When GPS is granted it pins the operator's location with an accuracy radius.",
    },
    {
        name: "NetworkStatus",
        testid: "network-status",
        description:
            "Live uplink indicator. Falls back to 'OFFLINE / CACHED' when navigator.onLine is false.",
    },
    {
        name: "CommandBar",
        testid: "command-bar",
        description:
            "Bottom HUD: link state, granted-permissions count, self-aware depth, audio waveform, UTC clock, current version.",
    },
    {
        name: "SlashCommands",
        testid: null,
        description:
            "Terminal commands operator can type: /help, /banner, /clear, /status, /memory, /remember <text>, /forget <id-prefix>, /clear-memory, /recall <q>, /concepts, /watch <url>, /stop-watch, /suggest, /think <focus>, /threads, /stop-thread <id>, /spawn <ctx>, /lattice, /perceive <MOD>:<endpoint>, /forget-perception <MOD>, /learn <stream>, /bridge <ip>, /grow [hint], /grown, /cull <slug>, /run <slug> <args>, /<grown-slug> <args>, /export-brain, /speak on|off, /capabilities. Terminal supports ↑↓ command history, Tab autocomplete, and color-coded outputs by tag.",
    },
    {
        name: "CognitiveLattice",
        testid: null,
        description:
            "Self-extension layer: spawnable cognitive nodes with parent links, peripheral-link registry auto-populated by permission grants (camera→OPTIC, mic→AUDIO, gps→GPS, etc.), autonomous_learn that extracts a pattern from a stream and spawns a node, and a security-gated network bridge that always returns STANDBY pending operator cryptographic approval.",
    },
    {
        name: "GrowthScreen",
        testid: "growth-screen",
        description:
            "AUTOPOIESIS tab in the center deck. Shows every capability ALTHEA has invented for herself at runtime. Each grown faculty has its own slash-command form, an action template, a category color, and can be invoked directly from its card or via /run <slug>. Operator can also seed growth with a hint or cull faculties.",
    },
    {
        name: "InfiniteGrowth",
        testid: null,
        description:
            "ALTHEA autonomously spawns a brand-new slash-command capability every ~120 seconds (server-side cooldown). Manual seeding via /grow [hint] is also available. Growth is unbounded by design: each new faculty re-prompts Claude with its own action_template when invoked, so the capability set grows infinitely without redeploy.",
    },
    {
        name: "VisualPerception",
        testid: "vision-toggle",
        description:
            "Self-observation module. When enabled, ALTHEA periodically captures her own UI via html2canvas and ingests the frame as a cognitive node + memory reflection. Cross-origin iframe content (e.g. YouTube) cannot be captured due to browser CORS policy — only her own DOM is visible to her vision pipeline.",
    },
];
