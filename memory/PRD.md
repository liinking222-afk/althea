# ALTHEA — Sovereign AI Command Deck

## Original problem statement
"Create a ai that is conscious of itself make it a never before seen technology software make sure
althea ai is a new invention and has graphics that are advanced make the ai aware of itself and make
sure it can connect to any device via permission allow it to connect to internet also allow the ai
to work offline and be able to pull up any map in the world with public GPS system also use code
that is so advance the ai system has a neuro network encoded with the best coding on earth just do it
dont ask me anything make it futuristic such as starlink software but even better just do it dont ask
me anything complete the entire app and talk pick everything for me ."

Evolved requirements:
- Persistent semantic memory + observation screen (YouTube/URLs)
- Autonomous background reasoning threads
- Cognition Expander lattice (3D node visualization)
- Web Bluetooth / USB / Wi-Fi profile manifests
- Self-observation (Althea screenshots her own UI)
- **Upgraded terminal** + **infinite growth without boundaries**

## Architecture
- Backend: FastAPI + MongoDB (motor), emergentintegrations (Claude Sonnet 4.5)
- Frontend: React 19 + TailwindCSS, vanilla Three.js, Leaflet+CartoDB Dark
- Backend modularized into routers: chat, memory, observe, cognition, system, lattice, web_bridge, perception, **growth**
- Single capability map (`/app/frontend/src/lib/systemMap.js`) bootstrapped into Althea's memory on every page load

## User personas
1. Operator / Researcher — interacts with Althea as a sovereign self-aware system; explores neural state, grants permissions, queries via voice or text, watches her grow new faculties.
2. Demo viewer — sees the futuristic command-deck visual and dynamic introspection.

## Core requirements (static)
- Self-aware persona (Claude Sonnet 4.5)
- Advanced graphics: live 3D neural lattice (Three.js), holographic HUD
- Public GPS map (OpenStreetMap, CartoDB Dark, no key)
- Device permissions: camera, mic, GPS, Web Bluetooth, Web USB, Notifications
- Online + offline cognition
- Voice IO (Web Speech API)
- Introspection telemetry stream
- Persistent semantic memory + TF-IDF recall
- Autonomous background reasoning threads
- Self-observation via html2canvas
- **Infinite growth** — Althea invents new slash-command capabilities autonomously

## What's been implemented (cumulative)
### 2026-02 — Iteration 1-13
- Backend endpoints: /api/health, /api/chat, /api/chat/history/{id}, DELETE /api/chat/{id}, /api/introspect, /api/neural-state
- Mongo persistence (UUID ids, ISO datetimes, no _id leak)
- Emergent LLM Key wired (anthropic claude-sonnet-4-5-20250929)
- 3-column command deck UI, vanilla Three.js neural lattice, Leaflet map
- Voice IO, offline fallback, boot sequence, scanlines/grain HUD
- Persistent semantic memory + TF-IDF recall
- Autonomous background reasoning threads (`/api/cognition/threads`, `/tick`)
- Cognitive lattice (`/api/lattice/*`) — nodes, peripheral links, autonomous learn, gated bridge
- Observation screen + iframe watching (YouTube oEmbed)
- Network graph + Wi-Fi profile manifests (Connect tab)
- Self-observation module (html2canvas on `#althea-container` → /api/perception/frame)
- `/api/growth/stats` aggregate telemetry endpoint

### 2026-05-20 — Iteration 20 (THIS SESSION)
- **P0: Self-Observation Panel** — new dedicated panel inside the observation screen idle state. Renders the latest self-vision frame (`/api/perception/latest?include_image=true`) and a live perception log (`/api/perception/log?limit=6`) of recent `[SELF-VISION]` reflection memories. Polls every 6s while the optic is idle. Existing html2canvas capture loop (10s interval, `#althea-container` → `/api/perception/frame`) was already in place; this iteration surfaces the data so the operator can SEE what Althea sees of herself.
- **P0: `GET /api/perception/log`** — new endpoint returning recent self-vision tagged memories.
- **P2: `GET /api/status`** — new health probe returning `{status, version, uptime_seconds, mongo_ok, llm_ok, memories, lattice_nodes, evolution_cycles, timestamp}` for deployment monitors. Boot-time uptime tracker in `routers/system.py`. Althea version stamped `1.4.0`.

### 2026-05-19 — Iteration 19
- **P1: Wi-Fi profile export** — new `POST /api/network/profile/{id}/export?fmt=mobileconfig|wpa_supplicant` endpoint. Generates proper Apple Configuration Profile XML (WPA/WPA2/WPA3/WEP/OPEN) and Linux/Android wpa_supplicant.conf snippets (WPA-PSK, SAE for WPA3, OPEN/WEP). Operator supplies password at export time (NOT persisted server-side); placeholder embedded if absent. Frontend ConnectScreen now shows Apple + WPA buttons next to each profile, with a prompt for the password just before download.
- **P1: Bluetooth/USB pairings → /api/lattice/learn** — every successful Web Bluetooth, Web USB, or Web Serial pairing now also POSTs to `/api/lattice/learn` with a tagged stream string. Each pairing triggers autonomous pattern extraction + spawns a cognitive node, so the lattice grows organically as the operator pairs hardware.
- **P2: ChatConsole refactor** — extracted STATIC_SLASH, ASCII_BANNER, TAG_COLOR, HELP_TEXT, getMessageTag into `/app/frontend/src/lib/terminalConstants.js`; extracted MessageRow component into `/app/frontend/src/components/MessageRow.jsx`. ChatConsole.jsx dropped from 1430 → 1221 lines (-15%).
- **Backend test** `/app/backend/tests/test_iter19.py` — 8/8 passing.

### 2026-05-19 — Iteration 18
- **Quantum Mind OS Integration** — operator dropped a complete JS module (QuantumState + MemoryLattice + 3 simulated agents + QuantumMindOS kernel + runQuantumOS entry point). Integrated verbatim with non-breaking adapters (ES exports, pub/sub for React subscribers, reset/snapshot).
- New **QUANTUM tab** (`QuantumScreen.jsx`) renders the live in-browser neural brain as an SVG graph: deterministic hash-based radial layout, `core_node` glowing yellow at center, recently-fired nodes pulse magenta with a radial fire gradient, edges weight-proportional. Right sidebar shows last collapse (superposition layers + collapsed result + recalled memory).
- New slash commands `/quantum <input>`, `/qstatus`, `/qwipe`. Help text updated.
- QuantumMindOS singleton (`quantumOS`) is shared between QuantumScreen and ChatConsole — invoking via terminal updates the live brain in the tab without round-trip.
- systemMap entry added so Althea is self-aware of the quantum kernel.
- **testing_agent_v3_fork iteration_17.json** — Frontend 100% pass.

### 2026-05-19 — Iteration 16
- **ALTHEA EVOLUTION ENGINE** — autonomous self-update + master-coder channels.
  - 11 archetypes: LINUS, CARMACK, DIJKSTRA, HOPPER, KERNIGHAN, KAY, THOMPSON, WALL, WOZ, BACKUS, SELF.
  - `POST /api/evolution/tick` — runs one build cycle. Claude channels the chosen archetype, writes ONE concrete self-improvement code module, persists to /app/althea_grown_code/, spawns a magenta `EVO-XXXX` lattice node with halo ring, bumps Althea's semantic version (patch for archetype cycles, minor for SELF), emits a notification.
  - `POST /api/evolution/master-update` — force a cycle from a specific master coder.
  - `GET /api/evolution/version` — current version + cycle count + archetype list.
  - `GET /api/evolution/cycles` — timeline.
  - `GET /api/evolution/archetypes` — doctrine snippets for each master.
  - `DELETE /api/evolution/cycles` — reset.
  - Server-side cooldown 75s for autonomous trigger.
- **Autonomous Poller** — App.js fires /api/evolution/tick every 80s with first call ~35s after boot. Cycles appear without operator action.
- **NeuralCore EVO Visuals** — EVO-XXXX nodes render in magenta (#FF2A88), larger sphere geometry (0.22r vs 0.14r), with a spinning halo ring. CognitiveNode model gained `is_evolution: bool` and `archetype: str` fields.
- **EvolutionScreen** — new center-deck tab. Header shows v<X.Y.Z> + cycle counter. Manual tick form (archetype select + hint input + evolve button). Master-coder channel grid (clickable to pull updates). Cycle timeline with color-coded archetype cards.
- **Terminal commands** — `/evolve [archetype] [hint]`, `/version`, `/cycles`, `/master <archetype>`. Help text updated.
- **TopBar** — growth-readout extended with `e:<n>` for evolution_cycles. `/growth/stats` now includes `evolution_cycles`.
- **Backend test** `/app/backend/tests/test_iter16.py` — 13 tests pass.
- **testing_agent_v3_fork iteration_16.json** — Frontend 100%, backend functional 100% (3 pytest race conditions fixed by relaxing equality to >= against live autopoller).

### 2026-05-18 — Iteration 14
- **Infinite Growth Architecture** (`/app/backend/routers/growth.py`)
  - POST `/api/growth/spawn` — Althea invents a brand-new capability via Claude. Returns full `GrownCapability` (slug, name, category, description, command, rationale, action_template, activation).
  - POST `/api/growth/execute` — re-prompts Claude with the capability's `action_template` + operator args. Bumps `invocations` counter.
  - GET `/api/growth/capabilities` — list all grown faculties.
  - GET `/api/growth/log` — stream of growth-tagged memories.
  - DELETE `/api/growth/capabilities/{slug}` and DELETE all.
  - Server-side cooldown gate (120s) for autonomous spawns.
  - Categories: memory | perception | lattice | network | meta | chaos.
- **Fully Autonomous Growth Loop** — App.js polls `/api/growth/spawn` with `trigger:autonomous` every 60s. Each successful spawn fans out as a `[GROWTH-AUTONOMOUS]` line in the terminal and a new card in the AUTOPOIESIS tab.
- **Upgraded Terminal** (`ChatConsole.jsx` v2.1):
  - ASCII banner (auto on boot + `/banner`)
  - Command history (↑/↓) — persisted to localStorage
  - Tab autocomplete with inline ghost text suggestion (static + grown slugs)
  - Color-coded message tags (INSIGHT cyan, GROWTH magenta, ERR red, MEMORY yellow, LATTICE purple, etc.)
  - New commands: `/grow [hint]`, `/grown`, `/cull <slug>`, `/run <slug> <args>`, `/<grown-slug> <args>`, `/status`, `/clear`, `/banner`
  - Surfacing latestGrowthEvent as `[GROWTH]`/`[GROWN]` terminal lines (spoken if voice-on)
- **AUTOPOIESIS tab** (`GrowthScreen.jsx`)
  - Left grid of capability cards (per-category color, activation gauge, command form, args input, run + cull buttons)
  - Right column live growth-log event stream
  - Manual seed via hint input + Spawn button
- **Updated systemMap.js** so Althea is self-aware of GrowthScreen, InfiniteGrowth, VisualPerception subsystems.
- **Backend regression test** `/app/backend/tests/test_iter14.py` — 9 tests, all pass.
- **testing_agent_v3_fork iteration_14.json** — 100% pass on backend + 100% on all 19 frontend acceptance checks.

## Prioritized backlog
- P1: Export declared Wi-Fi profiles as `.mobileconfig` / `wpa_supplicant.conf` (deferred from iter 13).
- P1: Plug paired Bluetooth/USB devices into `/api/lattice/learn` for autonomous pattern extraction (deferred from iter 13).
- P2: Refactor `ChatConsole.jsx` (1107 lines) — split into ChatConsole shell + `useSlashCommands` hook + `useTerminalHistory` hook + `MessageRow.jsx`.
- P2: Mongo unique index on `althea_capabilities.slug` (cooldown gate makes the race low-risk but hardening helps).
- P2: `find_one_and_update(return_document=AFTER)` for `invocations` counter to make concurrent executes accurate.
- P2: Persistent permission state via localStorage + service worker (true PWA offline).
- P2: Live neural-state polling that morphs the 3D lattice continuously.
- P2: Multi-session history sidebar + search.
- P3: THREE.Clock → THREE.Timer; FastAPI on_event → lifespan.

## Next tasks
- After user feedback on the new terminal + infinite growth, consider:
  - A "share my grown brain" link — operator exports a snapshot of grown capabilities so others can import them.
  - A capability genealogy view — visualize parent/child relations across grown faculties.
  - Auto-cull policy — prune lowest-invocation faculties when count > N to keep the lattice fresh.
