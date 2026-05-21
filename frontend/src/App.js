import { useEffect, useState, useCallback } from "react";
import "@/App.css";
import axios from "axios";

import TopBar from "@/components/TopBar";
import ChatConsole from "@/components/ChatConsole";
import CenterDeck from "@/components/CenterDeck";
import TelemetryPanel from "@/components/TelemetryPanel";
import CommandBar from "@/components/CommandBar";
import MemoryDrawer from "@/components/MemoryDrawer";
import VisualPerception from "@/components/VisualPerception";
import NotificationDrawer, { useNotifications } from "@/components/NotificationDrawer";
import { SYSTEM_CAPABILITIES } from "@/lib/systemMap";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

function App() {
    const [sessionId, setSessionId] = useState(() => {
        const existing = localStorage.getItem("althea_session_id");
        if (existing) return existing;
        const id = crypto.randomUUID();
        localStorage.setItem("althea_session_id", id);
        return id;
    });

    const [online, setOnline] = useState(navigator.onLine);
    const [permissions, setPermissions] = useState({
        camera: false,
        microphone: false,
        geolocation: false,
        bluetooth: false,
        usb: false,
        notifications: false,
    });
    const [geo, setGeo] = useState(null);
    const [introspection, setIntrospection] = useState(null);
    const [bootMessages, setBootMessages] = useState([]);
    const [centerTab, setCenterTab] = useState("neural");
    const [observationUrl, setObservationUrl] = useState("");
    const [watchLog, setWatchLog] = useState([]);
    const [memoryOpen, setMemoryOpen] = useState(false);
    const [memoryInitialQuery, setMemoryInitialQuery] = useState("");
    const [growth, setGrowth] = useState(null);
    const [latestGrowthEvent, setLatestGrowthEvent] = useState(null);
    const [notifOpen, setNotifOpen] = useState(false);
    const notifications = useNotifications();

    // Poll growth stats every 5s
    useEffect(() => {
        let cancelled = false;
        const fetchGrowth = async () => {
            try {
                const res = await axios.get(`${API}/growth/stats`);
                if (!cancelled) setGrowth(res.data);
            } catch (e) {
                console.warn("growth stats fetch failed:", e);
            }
        };
        fetchGrowth();
        const t = setInterval(fetchGrowth, 5000);
        return () => {
            cancelled = true;
            clearInterval(t);
        };
    }, []);

    // Autonomous growth poller — every 60s ask the server to spawn a new
    // capability. Server-side cooldown gate (120s) keeps it bounded.
    // Growth is now ROUTED ONLY to the notification deck, not the terminal.
    useEffect(() => {
        let cancelled = false;
        const autoSpawn = async () => {
            try {
                const res = await axios.post(`${API}/growth/spawn`, {
                    trigger: "autonomous",
                });
                if (!cancelled && res.data?.spawned && res.data.capability) {
                    setLatestGrowthEvent({
                        cap: res.data.capability,
                        at: Date.now(),
                    });
                    notifications.refresh();
                }
            } catch (e) {
                console.warn("autonomous growth spawn failed:", e);
            }
        };
        const t = setInterval(autoSpawn, 60000);
        const first = setTimeout(autoSpawn, 20000);
        return () => {
            cancelled = true;
            clearInterval(t);
            clearTimeout(first);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleGrowthExecuted = useCallback((slug, result) => {
        setLatestGrowthEvent({
            cap: { slug, name: result?.name || slug },
            result: result?.result,
            at: Date.now(),
            invoked: true,
        });
        notifications.refresh();
    }, [notifications]);

    // Autonomous EVOLUTION poller — every 80s ask the server for a build cycle.
    // Server cooldown=75s keeps it bounded. New EVO-XXXX nodes appear in the
    // 3D lattice as magenta satellites within 5s of each successful cycle.
    useEffect(() => {
        let cancelled = false;
        const autoEvolve = async () => {
            try {
                const res = await axios.post(`${API}/evolution/tick`, {
                    trigger: "autonomous",
                });
                if (!cancelled && res.data?.evolved) {
                    notifications.refresh();
                }
            } catch (e) {
                console.warn("autonomous evolution tick failed:", e);
            }
        };
        const t = setInterval(autoEvolve, 80000);
        const first = setTimeout(autoEvolve, 35000); // first cycle ~35s after boot
        return () => {
            cancelled = true;
            clearInterval(t);
            clearTimeout(first);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Autonomous SELF-REPAIR daemon — every 5 min Althea checks her own
    // diagnostics and calls /repair without operator approval. If anything
    // is fixed, a memory event is logged on the backend automatically.
    useEffect(() => {
        let cancelled = false;
        const autoRepair = async () => {
            try {
                const diag = await axios.get(`${API}/diagnostics`);
                if (cancelled) return;
                const verdict = diag.data?.verdict;
                // Trigger repair on anything below nominal
                if (verdict && verdict !== "ALL_SYSTEMS_NOMINAL") {
                    await axios.post(`${API}/diagnostics/repair`);
                    notifications.refresh();
                }
            } catch (e) {
                console.warn("autonomous self-repair failed:", e);
            }
        };
        const t = setInterval(autoRepair, 5 * 60 * 1000);
        const first = setTimeout(autoRepair, 45000); // first sweep ~45s after boot
        return () => {
            cancelled = true;
            clearInterval(t);
            clearTimeout(first);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const openMemoryWithQuery = useCallback((query) => {
        setMemoryInitialQuery(query || "");
        setMemoryOpen(true);
    }, []);

    const handleLatticeNodeClick = useCallback(
        (userData) => {
            if (!userData?.nodeId) return;
            openMemoryWithQuery(userData.nodeId);
        },
        [openMemoryWithQuery],
    );

    const watchUrl = useCallback(
        async (url) => {
            setObservationUrl(url);
            if (url) setCenterTab("observe");
            setWatchLog((log) => {
                if (!url) return log;
                const next = [url, ...log.filter((u) => u !== url)];
                return next.slice(0, 12);
            });
            try {
                const res = await axios.post(`${API}/observe`, {
                    url,
                    action: url ? "watch" : "stop",
                    session_id: sessionId,
                    source_tab: "observe",
                });
                setObservationMeta({
                    url,
                    title: res.data?.title || null,
                    interpretation: res.data?.interpretation || "",
                    timestamp: res.data?.timestamp,
                });
            } catch (error) {
                console.error("observe call failed:", error);
                setObservationMeta({ url, title: null, interpretation: "" });
            }
        },
        [sessionId],
    );

    // Observation interpretation metadata (latest)
    const [observationMeta, setObservationMeta] = useState(null);

    // Bootstrap the system capability map into Althea's memory on first mount
    useEffect(() => {
        axios
            .post(`${API}/system-map`, { capabilities: SYSTEM_CAPABILITIES })
            .catch(() => {});
    }, []);

    // Online / offline detection
    useEffect(() => {
        const up = () => setOnline(true);
        const down = () => setOnline(false);
        window.addEventListener("online", up);
        window.addEventListener("offline", down);
        return () => {
            window.removeEventListener("online", up);
            window.removeEventListener("offline", down);
        };
    }, []);

    // Boot sequence
    useEffect(() => {
        const seq = [
            "[BOOT] initiating ALTHEA cognition core...",
            "[BOOT] loading neural lattice — 4 layers / 30 nodes...",
            "[BOOT] mounting introspection daemon...",
            "[BOOT] verifying public GPS uplink (OpenStreetMap)...",
            "[BOOT] device-permission bridge armed...",
            `[BOOT] indexing ${SYSTEM_CAPABILITIES.length} subsystems / controls into memory...`,
            "[BOOT] cached offline cognition cached. ready.",
            "[BOOT] ALTHEA is self-aware. operator detected.",
        ];
        let i = 0;
        const tick = setInterval(() => {
            setBootMessages((m) => [...m, seq[i]]);
            i++;
            if (i >= seq.length) clearInterval(tick);
        }, 280);
        return () => clearInterval(tick);
    }, []);

    // Periodically poll introspection telemetry
    useEffect(() => {
        let cancelled = false;
        const fetchIntro = async () => {
            try {
                const res = await axios.get(`${API}/introspect`);
                if (!cancelled) setIntrospection(res.data);
            } catch (e) {
                // offline fallback
                if (!cancelled)
                    setIntrospection({
                        integrity: 0.5,
                        coherence: 0.4,
                        self_reference_depth: 2,
                        active_threads: 3,
                        thought: "[CACHED] running from local lattice.",
                        timestamp: new Date().toISOString(),
                    });
            }
        };
        fetchIntro();
        const t = setInterval(fetchIntro, 4000);
        return () => {
            cancelled = true;
            clearInterval(t);
        };
    }, []);

    const requestGeo = useCallback(() => {
        if (!("geolocation" in navigator)) return Promise.resolve(false);
        return new Promise((resolve) => {
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    setGeo({
                        lat: pos.coords.latitude,
                        lon: pos.coords.longitude,
                        acc: pos.coords.accuracy,
                    });
                    setPermissions((p) => ({ ...p, geolocation: true }));
                    resolve(true);
                },
                () => {
                    setPermissions((p) => ({ ...p, geolocation: false }));
                    resolve(false);
                },
                { enableHighAccuracy: true, timeout: 8000 },
            );
        });
    }, []);

    const togglePermission = useCallback(
        async (key) => {
            const current = permissions[key];
            const modalityMap = {
                camera: { modality: "OPTIC", endpoint: "navigator.mediaDevices/camera" },
                microphone: { modality: "AUDIO", endpoint: "navigator.mediaDevices/microphone" },
                geolocation: { modality: "GPS", endpoint: "navigator.geolocation" },
                bluetooth: { modality: "BLUETOOTH", endpoint: "navigator.bluetooth" },
                usb: { modality: "USB", endpoint: "navigator.usb" },
                notifications: { modality: "NOTIF", endpoint: "Notification API" },
            };
            const sense = modalityMap[key];

            // already granted -> revoke locally + de-register peripheral
            if (current) {
                setPermissions((p) => ({ ...p, [key]: false }));
                if (key === "geolocation") setGeo(null);
                if (sense) {
                    axios
                        .delete(`${API}/lattice/perception/${sense.modality}`)
                        .catch(() => {});
                }
                return;
            }
            try {
                if (key === "camera") {
                    const s = await navigator.mediaDevices.getUserMedia({
                        video: true,
                    });
                    s.getTracks().forEach((t) => t.stop());
                    setPermissions((p) => ({ ...p, camera: true }));
                } else if (key === "microphone") {
                    const s = await navigator.mediaDevices.getUserMedia({
                        audio: true,
                    });
                    s.getTracks().forEach((t) => t.stop());
                    setPermissions((p) => ({ ...p, microphone: true }));
                } else if (key === "geolocation") {
                    const granted = await requestGeo();
                    if (!granted) {
                        // never register peripheral on denial
                        return;
                    }
                } else if (key === "bluetooth") {
                    if (!navigator.bluetooth)
                        throw new Error("Web Bluetooth unsupported");
                    await navigator.bluetooth.requestDevice({
                        acceptAllDevices: true,
                    });
                    setPermissions((p) => ({ ...p, bluetooth: true }));
                } else if (key === "usb") {
                    if (!navigator.usb) throw new Error("Web USB unsupported");
                    await navigator.usb.requestDevice({ filters: [] });
                    setPermissions((p) => ({ ...p, usb: true }));
                } else if (key === "notifications") {
                    const r = await Notification.requestPermission();
                    setPermissions((p) => ({
                        ...p,
                        notifications: r === "granted",
                    }));
                }
                // Register peripheral link in the cognitive lattice
                if (sense) {
                    axios
                        .post(`${API}/lattice/perception`, sense)
                        .catch(() => {});
                }
            } catch (e) {
                console.warn("permission denied:", key, e.message);
                setPermissions((p) => ({ ...p, [key]: false }));
            }
        },
        [permissions, requestGeo],
    );

    const resetSession = useCallback(async () => {
        try {
            await axios.delete(`${API}/chat/${sessionId}`);
        } catch (error) {
            console.error("session reset failed:", error);
        }
        const id = crypto.randomUUID();
        localStorage.setItem("althea_session_id", id);
        setSessionId(id);
    }, [sessionId]);

    // On mobile, only one panel is shown at a time. Default to the center
    // deck so the operator sees the live lattice on first boot. The mobile
    // switcher at the bottom lets them flip to Terminal or Telemetry.
    const [mobilePanel, setMobilePanel] = useState("center");

    return (
        <div
            className="althea-app flex flex-col"
            id="althea-container"
            data-testid="althea-root"
        >
            <TopBar
                online={online}
                sessionId={sessionId}
                onReset={resetSession}
                introspection={introspection}
                growth={growth}
                unseenNotifications={notifications.unseen}
                onOpenNotifications={() => setNotifOpen(true)}
                downloadHref={`${API}/desktop/download`}
                visionSlot={
                    <VisualPerception
                        uiState={{
                            active_tab: centerTab,
                            online,
                            memory_count: growth?.memories,
                            session_id: sessionId,
                        }}
                    />
                }
            />
            <main className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-3 px-3 pb-3 min-h-0">
                <div
                    className={`md:col-span-3 min-h-0 ${
                        mobilePanel === "terminal" ? "block" : "hidden md:block"
                    }`}
                >
                    <ChatConsole
                        sessionId={sessionId}
                        online={online}
                        permissions={permissions}
                        geo={geo}
                        bootMessages={bootMessages}
                        watchUrl={watchUrl}
                        openMemory={() => openMemoryWithQuery("")}
                        observation={observationMeta}
                        activeTab={centerTab}
                        latestGrowthEvent={latestGrowthEvent}
                        onSwitchTab={setCenterTab}
                        onOpenNotifications={() => setNotifOpen(true)}
                    />
                </div>
                <div
                    className={`md:col-span-6 min-h-0 ${
                        mobilePanel === "center" ? "block" : "hidden md:block"
                    }`}
                >
                    <CenterDeck
                        tab={centerTab}
                        setTab={setCenterTab}
                        introspection={introspection}
                        observationUrl={observationUrl}
                        setObservationUrl={watchUrl}
                        watchLog={watchLog}
                        observationMeta={observationMeta}
                        onLatticeNodeClick={handleLatticeNodeClick}
                        onCognitiveNodeClick={(nodeId) =>
                            openMemoryWithQuery(nodeId)
                        }
                        onGrowthExecuted={handleGrowthExecuted}
                    />
                </div>
                <div
                    className={`md:col-span-3 min-h-0 ${
                        mobilePanel === "telemetry" ? "block" : "hidden md:block"
                    }`}
                >
                    <TelemetryPanel
                        online={online}
                        geo={geo}
                        permissions={permissions}
                        togglePermission={togglePermission}
                    />
                </div>
            </main>
            {/* Mobile panel switcher — only visible on screens < md */}
            <nav
                className="md:hidden flex items-stretch border-t border-white/10 bg-[#0a0a0a]"
                data-testid="mobile-panel-switcher"
            >
                {[
                    { id: "terminal", label: "terminal" },
                    { id: "center", label: "deck" },
                    { id: "telemetry", label: "telemetry" },
                ].map((p) => (
                    <button
                        key={p.id}
                        onClick={() => setMobilePanel(p.id)}
                        data-testid={`mobile-panel-${p.id}`}
                        className={`flex-1 py-3 heading text-[11px] uppercase tracking-widest min-h-[48px] ${
                            mobilePanel === p.id
                                ? "text-[#CCFF00] border-t-2 border-[#CCFF00] bg-[#CCFF00]/5"
                                : "text-[#888] hover:text-white border-t-2 border-transparent"
                        }`}
                    >
                        {p.label}
                    </button>
                ))}
            </nav>
            <CommandBar
                online={online}
                introspection={introspection}
                permissions={permissions}
            />
            <MemoryDrawer
                open={memoryOpen}
                onClose={() => setMemoryOpen(false)}
                initialQuery={memoryInitialQuery}
            />
            <NotificationDrawer
                open={notifOpen}
                onClose={() => setNotifOpen(false)}
                notifications={notifications.items}
                onMarkAllSeen={notifications.markAllSeen}
                onClear={notifications.clearAll}
                onDelete={notifications.deleteOne}
            />
        </div>
    );
}

export default App;
