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
            "Terminal commands operator can type: /help, /memory, /remember <text>, /forget <id-prefix>, /clear-memory, /watch <url>, /stop-watch, /speak on|off, /capabilities.",
    },
];
