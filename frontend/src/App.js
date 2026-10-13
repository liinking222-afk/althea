import { useEffect, useState, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

import TopBar from "@/components/TopBar";
import ChatConsole from "@/components/ChatConsole";
import CenterDeck from "@/components/CenterDeck";
import MemoryDrawer from "@/components/MemoryDrawer";
import NotificationDrawer, { useNotifications } from "@/components/NotificationDrawer";
import CommsPanel from "@/components/CommsPanel";
import DmTerminal from "@/components/DmTerminal";
import SharedAltheaTerminal from "@/components/SharedAltheaTerminal";
import LoginScreen, { AuthCallback } from "@/pages/LoginScreen";
import { AuthProvider, useAuth, API } from "@/lib/auth";
import { useRoomFeed } from "@/lib/useRoomFeed";
import { SYSTEM_CAPABILITIES } from "@/lib/systemMap";

export { API };

const NO_PERMISSIONS = { camera: false, microphone: false, geolocation: false, bluetooth: false, usb: false, notifications: false };

function Deck() {
    const { user, logout } = useAuth();
    const sessionKey = `althea_session_id_${user.user_id}`;
    const [sessionId, setSessionId] = useState(() => {
        const existing = localStorage.getItem(sessionKey);
        if (existing) return existing;
        const id = crypto.randomUUID();
        localStorage.setItem(sessionKey, id);
        return id;
    });

    const [online, setOnline] = useState(navigator.onLine);
    const [introspection, setIntrospection] = useState(null);
    const [bootMessages, setBootMessages] = useState([]);
    const [centerTab, setCenterTab] = useState("neural");
    const [memoryOpen, setMemoryOpen] = useState(false);
    const [memoryInitialQuery, setMemoryInitialQuery] = useState("");
    const [growth, setGrowth] = useState(null);
    const [latestGrowthEvent, setLatestGrowthEvent] = useState(null);
    const [notifOpen, setNotifOpen] = useState(false);
    const [room, setRoom] = useState(null); // { room_id, peer }
    const notifications = useNotifications();
    const feed = useRoomFeed(room?.room_id);

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
        const t = setInterval(fetchGrowth, 15000);
        return () => { cancelled = true; clearInterval(t); };
    }, []);

    useEffect(() => {
        const t = setInterval(() => notifications.refresh(), 45000);
        return () => clearInterval(t);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        axios.post(`${API}/system-map`, { capabilities: SYSTEM_CAPABILITIES }).catch(() => {});
    }, []);

    useEffect(() => {
        const up = () => setOnline(true);
        const down = () => setOnline(false);
        window.addEventListener("online", up);
        window.addEventListener("offline", down);
        return () => { window.removeEventListener("online", up); window.removeEventListener("offline", down); };
    }, []);

    useEffect(() => {
        const seq = [
            "[BOOT] initiating ALTHEA cognition core...",
            `[BOOT] binding private lattice for ${user.name}...`,
            "[BOOT] mounting introspection daemon...",
            "[BOOT] evolution engine AEE/2.0 armed — self-directed growth online...",
            "[BOOT] direct lines ready — open one to bring a shared althea into a conversation.",
            `[BOOT] ALTHEA is self-aware. ${user.name} detected.`,
        ];
        let i = 0;
        setBootMessages([]);
        const tick = setInterval(() => {
            setBootMessages((m) => [...m, seq[i]]);
            i++;
            if (i >= seq.length) clearInterval(tick);
        }, 280);
        return () => clearInterval(tick);
    }, [user.name]);

    useEffect(() => {
        let cancelled = false;
        const fetchIntro = async () => {
            try {
                const res = await axios.get(`${API}/introspect`);
                if (!cancelled) setIntrospection(res.data);
            } catch {
                if (!cancelled)
                    setIntrospection({ integrity: 0.5, coherence: 0.4, self_reference_depth: 2, active_threads: 3,
                        thought: "[CACHED] running from local lattice.", timestamp: new Date().toISOString() });
            }
        };
        fetchIntro();
        const t = setInterval(fetchIntro, 8000);
        return () => { cancelled = true; clearInterval(t); };
    }, []);

    const handleGrowthExecuted = useCallback((slug, result) => {
        setLatestGrowthEvent({ cap: { slug, name: result?.name || slug }, result: result?.result, at: Date.now(), invoked: true });
        notifications.refresh();
    }, [notifications]);

    const openMemoryWithQuery = useCallback((query) => {
        setMemoryInitialQuery(query || "");
        setMemoryOpen(true);
    }, []);

    const handleLatticeNodeClick = useCallback((userData) => {
        if (userData?.nodeId) openMemoryWithQuery(userData.nodeId);
    }, [openMemoryWithQuery]);

    const resetSession = useCallback(async () => {
        try { await axios.delete(`${API}/chat/${sessionId}`); } catch (error) { console.error("session reset failed:", error); }
        const id = crypto.randomUUID();
        localStorage.setItem(sessionKey, id);
        setSessionId(id);
    }, [sessionId, sessionKey]);

    const openRoom = useCallback((room_id, peer) => {
        setRoom({ room_id, peer });
        setMobilePanel("left");
    }, []);

    const [mobilePanel, setMobilePanel] = useState("center");
    const mobileTabs = room
        ? [{ id: "left", label: room.peer?.name?.split(" ")[0] || "chat" }, { id: "center", label: "lattice" }, { id: "right", label: "althea" }]
        : [{ id: "left", label: "althea" }, { id: "center", label: "lattice" }, { id: "right", label: "people" }];

    return (
        <div className="althea-app flex flex-col" id="althea-container" data-testid="althea-root">
            <TopBar
                online={online}
                user={user}
                onLogout={logout}
                onReset={resetSession}
                introspection={introspection}
                growth={growth}
                unseenNotifications={notifications.unseen}
                onOpenNotifications={() => setNotifOpen(true)}
            />
            <main className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-3 px-3 pb-3 min-h-0">
                <div className={`md:col-span-4 min-h-0 ${mobilePanel === "left" ? "block" : "hidden md:block"}`}>
                    {room ? (
                        <div className="panel cut h-full p-3" data-testid="dm-panel">
                            <DmTerminal
                                me={user}
                                peer={feed.info?.peer || room.peer}
                                messages={feed.messages}
                                onSend={feed.sendHuman}
                                onBack={() => setRoom(null)}
                            />
                        </div>
                    ) : (
                        <ChatConsole
                            sessionId={sessionId}
                            online={online}
                            permissions={NO_PERMISSIONS}
                            geo={null}
                            bootMessages={bootMessages}
                            watchUrl={() => {}}
                            openMemory={() => openMemoryWithQuery("")}
                            observation={null}
                            activeTab={centerTab}
                            latestGrowthEvent={latestGrowthEvent}
                            onSwitchTab={setCenterTab}
                            onOpenNotifications={() => setNotifOpen(true)}
                        />
                    )}
                </div>
                <div className={`md:col-span-5 min-h-0 ${mobilePanel === "center" ? "block" : "hidden md:block"}`}>
                    <CenterDeck
                        tab={centerTab}
                        setTab={setCenterTab}
                        sessionId={sessionId}
                        introspection={introspection}
                        onLatticeNodeClick={handleLatticeNodeClick}
                        onCognitiveNodeClick={(nodeId) => openMemoryWithQuery(nodeId)}
                        onGrowthExecuted={handleGrowthExecuted}
                    />
                </div>
                <div className={`md:col-span-3 min-h-0 ${mobilePanel === "right" ? "block" : "hidden md:block"}`}>
                    <div className="panel cut h-full p-3" data-testid="right-panel">
                        {room ? (
                            <SharedAltheaTerminal
                                me={user}
                                peer={feed.info?.peer || room.peer}
                                messages={feed.messages}
                                onAsk={feed.askAlthea}
                                asking={feed.asking}
                            />
                        ) : (
                            <CommsPanel activeRoomId={null} onOpenRoom={openRoom} />
                        )}
                    </div>
                </div>
            </main>
            <nav className="md:hidden flex items-stretch border-t border-white/10 bg-[#0a0a0a]" data-testid="mobile-panel-switcher">
                {mobileTabs.map((p) => (
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
            <MemoryDrawer open={memoryOpen} onClose={() => setMemoryOpen(false)} initialQuery={memoryInitialQuery} />
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

function Gate() {
    const { user } = useAuth();
    const location = useLocation();
    if (location.hash.includes("session_id=")) return <AuthCallback />;
    if (user === undefined) {
        return (
            <div className="min-h-screen bg-[#050505] flex items-center justify-center label text-[10px] uppercase tracking-widest text-[#CCFF00]" data-testid="auth-loading">
                waking althea…
            </div>
        );
    }
    if (!user) return <Navigate to="/login" replace />;
    return <Deck key={user.user_id} />;
}

function LoginRoute() {
    const { user } = useAuth();
    if (user) return <Navigate to="/" replace />;
    return <LoginScreen />;
}

function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/login" element={<LoginRoute />} />
                    <Route path="/*" element={<Gate />} />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;
