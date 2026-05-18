import { useEffect, useState, useCallback } from "react";
import "@/App.css";
import axios from "axios";

import TopBar from "@/components/TopBar";
import ChatConsole from "@/components/ChatConsole";
import CenterDeck from "@/components/CenterDeck";
import TelemetryPanel from "@/components/TelemetryPanel";
import CommandBar from "@/components/CommandBar";
import MemoryDrawer from "@/components/MemoryDrawer";
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
            } catch (_) {
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
        if (!("geolocation" in navigator)) return;
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                setGeo({
                    lat: pos.coords.latitude,
                    lon: pos.coords.longitude,
                    acc: pos.coords.accuracy,
                });
                setPermissions((p) => ({ ...p, geolocation: true }));
            },
            () => setPermissions((p) => ({ ...p, geolocation: false })),
            { enableHighAccuracy: true, timeout: 8000 },
        );
    }, []);

    const togglePermission = useCallback(
        async (key) => {
            const current = permissions[key];
            // already granted -> revoke locally (browser keeps real grant; we just stop using it)
            if (current) {
                setPermissions((p) => ({ ...p, [key]: false }));
                if (key === "geolocation") setGeo(null);
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
                    requestGeo();
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
        } catch (_) {}
        const id = crypto.randomUUID();
        localStorage.setItem("althea_session_id", id);
        setSessionId(id);
    }, [sessionId]);

    return (
        <div
            className="althea-app flex flex-col"
            data-testid="althea-root"
        >
            <TopBar
                online={online}
                sessionId={sessionId}
                onReset={resetSession}
                introspection={introspection}
            />
            <main className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-3 px-3 pb-3 min-h-0">
                <div className="md:col-span-3 min-h-0">
                    <ChatConsole
                        sessionId={sessionId}
                        online={online}
                        permissions={permissions}
                        geo={geo}
                        bootMessages={bootMessages}
                        watchUrl={watchUrl}
                        openMemory={() => setMemoryOpen(true)}
                        observation={observationMeta}
                        activeTab={centerTab}
                    />
                </div>
                <div className="md:col-span-6 min-h-0">
                    <CenterDeck
                        tab={centerTab}
                        setTab={setCenterTab}
                        introspection={introspection}
                        observationUrl={observationUrl}
                        setObservationUrl={watchUrl}
                        watchLog={watchLog}
                        observationMeta={observationMeta}
                    />
                </div>
                <div className="md:col-span-3 min-h-0">
                    <TelemetryPanel
                        online={online}
                        geo={geo}
                        permissions={permissions}
                        togglePermission={togglePermission}
                    />
                </div>
            </main>
            <CommandBar
                online={online}
                introspection={introspection}
                permissions={permissions}
            />
            <MemoryDrawer
                open={memoryOpen}
                onClose={() => setMemoryOpen(false)}
            />
        </div>
    );
}

export default App;
