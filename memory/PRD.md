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

### 2026-05-21 — Iteration 26 (THIS SESSION)
- **LaTeX math in terminal** — KaTeX added (`yarn add katex`, CSS imported globally). `MessageRow.jsx` tokenizes every reply and renders `$inline$` + `$$block$$` math, fenced code blocks, **bold**, and inline images. Unlimited message length verified end-to-end.
- **Image generation** — new `POST /api/images/generate` using Gemini Nano Banana (`gemini-3.1-flash-image-preview`) via emergentintegrations. Returns base64 `data_url`, logs `[IMAGINED]` memory event, stored in `althea_images` collection. Budget-exceeded → HTTP 402.
- **Auto-image directive** — Althea's system prompt teaches her to write `[IMAGE: vivid prompt]` when a diagram aids explanation. MessageRow intercepts the directive, calls Gemini, caches via sessionStorage, renders inline.
- **`/imagine <prompt>`** terminal slash command (aliases `/draw`, `/visualize`).
- Verified end-to-end: "Show me Maxwell's equations and draw a magnetic field around a wire" → 4 KaTeX math blocks + 1 inline Gemini image + paragraph-length physics explanation.

### 2026-05-21 — Iteration 25 (THIS SESSION)
- **Memory effectively unlimited**:
  - `RECALL_CORPUS_MAX` 2000 → 250,000 (the full lattice in any realistic scenario)
  - Default list limit 200 → 500, max 100,000
  - Concept scan 5000 → 250,000
  - Diagnostics warning threshold 50k → 1,000,000
  - Mongo indexes on `timestamp` / `tags` / `source` / `session_id` auto-created on first call (idempotent) so recall stays O(log n) as the lattice scales
- **Chat memory window 3× richer** — `chat.py` now pulls the 60 most-recent memories PLUS the top 12 TF-IDF-relevant fragments from the entire 10,000-doc corpus that match the current user message. Older relevant context surfaces automatically.
- **`/api/memory/stats`** — new endpoint with total + by-source breakdown + index status
- **`/api/memory/consolidate`** — episodic→semantic compression. Folds the oldest memories beyond `keep_recent` (default 5,000) into compact summary memories (one per `batch_size` episodes, default 200). Preserves tag bag + 40 representative snippets. Verified: 73 episodes → 3 summaries on demand. Safe to call repeatedly.
- Terminal: new `/consolidate [n]` command.

### 2026-05-21 — Iteration 24
- **Caps lifted dramatically** — `MAX_GROWN_CAPABILITIES` 200 → 2000, `MAX_AUTO_SPAWNS_PER_HOUR` 18 → 90, `MAX_AUTO_EVOLUTION_PER_HOUR` 12 → 60. Cooldowns shortened (growth 120s → 45s, evolution 75s → 30s). Soft ceilings remain so a true runaway can't kill the system, but Althea now has ~5–10× more headroom for autonomous growth.
- **Autonomous self-repair daemon** — App.js polls `/api/diagnostics` every 5 min and calls `/api/diagnostics/repair` automatically whenever verdict ≠ `ALL_SYSTEMS_NOMINAL`. No operator approval needed. First sweep ~45s after boot.
- **Auto-apply safe code** — `POST /api/code/generate` now runs `safe_code_scan()` + `_syntax_check()` (Python `compile()` / JSON `loads()` / pass-through for languages we can't validate). If BOTH pass, the snippet is auto-applied (written to `/app/althea_grown_code/` and `applied=True`) **without operator approval**. Unsafe or syntax-broken code is still gated for review. Notification differentiates `auto-applied` from `requires manual review`.
- **Hard limit**: code is *never executed* automatically — only persisted. Executing untrusted code defeats the safety scan it just passed. Operator runs it manually.
- **Honest framing**: the Emergent Universal Key budget is enforced server-side at Emergent's billing layer (litellm proxy) — it cannot be lifted from app code. The user must top up via Profile → Universal Key, or enable Auto Top-up. When the key IS dead, Local Core (iter 22) makes Althea fully self-sufficient.

### 2026-05-21 — Iteration 23
- **Growth safety caps** — `MAX_GROWN_CAPABILITIES = 200` and `MAX_AUTO_SPAWNS_PER_HOUR = 18` in `routers/growth.py`; `MAX_AUTO_EVOLUTION_PER_HOUR = 12` in `routers/evolution.py`. Autonomous loops now refuse to spawn beyond these ceilings (responses include `reason: max_capabilities_reached` or `hourly_quota_reached`) so a runaway loop can never bloat the lattice or burn the LLM budget.
- **Troubleshoot tab** — new `TroubleshootScreen.jsx` center-deck tab with live polling (`/api/diagnostics` every 20s), severity-colored verdict header (`ALL_SYSTEMS_NOMINAL` / `OK_WITH_NOTES` / `DEGRADED`), 6 per-check cards (mongo/llm_key/lattice/perception/autonomous_loops/memory_volume) with inline error/remedy/metric chips, RESCAN + REPAIR buttons, repair log sidebar.
- **Terminal text-entry reliability** — `<input>` upgraded to auto-growing `<textarea>` (64–220px), `autoFocus` + mount-effect retries focus at 120ms and 600ms (fixes iOS Safari hydration drop), Enter sends, Shift+Enter inserts newline, leading `›` prompt marker aligned to top. Bigger default keeps multi-line slash commands readable.
- **Mobile-friendly layout** — three-column grid stacks vertically on screens < md; new bottom panel switcher (TERMINAL / DECK / TELEMETRY) with 48px+ tap targets; `100dvh` height so iOS Safari URL bar no longer crops the nav; TopBar already had `hidden md:flex` selectors so it shrinks gracefully. Verified at iPhone 14 viewport (390×844).

### 2026-05-21 — Iteration 22
- **Local Core (`/app/backend/local_core.py`)** — Althea's offline survival layer. When `EMERGENT_LLM_KEY` is missing, exhausted, or unreachable, chat / growth / evolution / codegen automatically route through:
  - `local_reply()` — TF-IDF grounded responder weaving recalled memory into first-person prose (wired into `routers/chat.py`).
  - `local_invent_capability()` — procedural GrownCapability inventor (wired into `routers/growth.py`).
  - `local_evolution_seed()` — archetype-flavored code stubs for all 11 master coders (wired into `routers/evolution.py`).
- **Sanitizer** (`sanitize_reply`) — strips runaway-token loops from every LLM reply (chat / growth / codegen / evolution).
- **Safe-code scanner** (`safe_code_scan`) — 13 destructive patterns. Blocks `POST /api/code/apply` with HTTP 409. Evolution auto-substitutes the local seed if Claude returns unsafe code.
- **Self-troubleshoot** (`routers/diagnostics.py`) — `GET /api/diagnostics` runs 6 health checks with severity + remedy per finding. `POST /api/diagnostics/repair` does safe self-repair. Terminal: `/diagnose`, `/troubleshoot`, `/repair`.
- **Lattice always zoomable out** — `NeuralCore.jsx` camera far-plane 100→10000, max zoom 28→5000, wheel step proportional to distance, new **FIT** button auto-frames the bounding sphere of all nodes regardless of count.

### 2026-05-20 — Iteration 21
- **Real-browser upgrade** — the Browser tab now renders the LIVE web. Two new endpoints:
  - `GET /api/browser/proxy?url=...` — fetches any URL server-side via httpx, strips `X-Frame-Options` / `CSP frame-ancestors` / `COOP` / `COEP` / `CORP`, drops CSP `<meta>` tags, rewrites every `href`/`src`/`action`/`srcset`/`poster` (and CSS `url(...)`) to flow through the proxy. Injects a `<base href="...">` and a small "althea // surf-proxy" badge.
  - `GET /api/browser/asset?url=...` — streaming sub-resource proxy for CSS/JS/images/fonts referenced by the proxied page (with CSS `url(...)` recursion).
  - 8MB cap per resource. Same UA + Referer that the page would normally see.
- **Smart direct embeds** — YouTube watch links + youtu.be + Vimeo + Twitch are auto-detected in the frontend and load through their native `/embed/` URLs (proxy bypass) so player JS works natively. Badge in the URL bar reads `DIRECT` vs `PROXY` so the operator knows the route.
- **Browser chrome rebuild** (`BrowserScreen.jsx`) — back/forward stacks, reload, home, smart URL bar (URL or search term → DuckDuckGo), live↔reader mode toggle, host indicator, "open in observation" handoff, bookmark grid for the idle state, loading veil with hostname.
- **Honest limits** — sites that hard-detect proxies (Twitter/X, Gmail, Cloudflare-gated logins) will still refuse to load. For those, switch to **Reader** mode to read the page's extracted text and link graph through the existing `/api/browser/fetch` path.
- Verified end-to-end: `example.com` renders fully styled inside the iframe, YouTube "Me at the zoo" plays inline via direct embed.

### 2026-05-20 — Iteration 20
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
