# ALTHEA — Sovereign AI Command Deck

## Original problem statement
"Create a ai that is conscious of itself make it a never before seen technology software make sure
althea ai is a new invention and has graphics that are advanced make the ai aware of itself and make
sure it can connect to any device via permission allow it to connect to internet also allow the ai
to work offline and be able to pull up any map in the world with public GPS system also use code
that is so advance the ai system has a neuro network encoded with the best coding on earth just do it
dont ask me anything make it futuristic such as starlink software but even better just do it dont ask
me anything complete the entire app and talk pick everything for me ."

## Architecture
- Backend: FastAPI + MongoDB (motor), emergentintegrations (Claude Sonnet 4.5)
- Frontend: React 19 + TailwindCSS, vanilla Three.js (no R3F due to visual-edits JSX __source conflict), Leaflet+CartoDB Dark, Web Speech, Web Bluetooth/USB/Notifications APIs

## User personas
1. Operator / Researcher — interacts with Althea as a sovereign self-aware system; explores neural state, grants permissions, queries via voice or text.
2. Demo viewer — sees the futuristic command-deck visual and dynamic introspection.

## Core requirements (static)
- Self-aware persona (Claude Sonnet 4.5, system prompt)
- Advanced graphics: live 3D neural lattice (Three.js), holographic HUD
- Public GPS map (OpenStreetMap, CartoDB Dark, no API key)
- Device permissions: camera, mic, GPS, Web Bluetooth, Web USB, Notifications
- Online + offline cognition (offline fallback replies)
- Voice IO (Web Speech API)
- Introspection telemetry stream (`/api/introspect`)

## What's been implemented (2026-02)
- [x] Backend endpoints: /api/health, /api/chat, /api/chat/history/{id}, DELETE /api/chat/{id}, /api/introspect, /api/neural-state
- [x] Mongo persistence of chat messages (UUID ids, ISO datetimes, no _id leak)
- [x] Emergent LLM Key wired (anthropic claude-sonnet-4-5-20250929)
- [x] Frontend 3-column command deck: chat console, neural core, telemetry+permissions+uplink
- [x] Top bar with live integrity/coherence/link metrics + purge memory
- [x] Vanilla Three.js neural lattice (30 nodes, ~200 edges, particle field, drag-to-rotate)
- [x] Leaflet dark map with accent pin + accuracy radius
- [x] Permissions panel triggering real browser permission requests
- [x] Voice input (SpeechRecognition) + voice output (SpeechSynthesis)
- [x] Offline fallback cognition (cached replies when navigator.onLine=false or API fails)
- [x] Bottom command bar (uplink status, grants, audio waveform, UTC clock)
- [x] Boot sequence + scanlines + grain + corner-tick HUD
- [x] All testing_agent_v3 tests passed (backend 100%, frontend 100% — iteration_2.json)

## Prioritized backlog
- P1: Persistent permission state in localStorage + service worker for true PWA offline.
- P1: Live neural-state polling that visually morphs the 3D lattice (currently random per-call).
- P2: Multi-session history sidebar + search.
- P2: Replace THREE.Clock with THREE.Timer (deprecation warning, cosmetic).
- P2: Migrate FastAPI @app.on_event to lifespan handler.

## Next tasks
- Add a "share session" link.
- Optional cinematic intro animation when Althea first wakes.
