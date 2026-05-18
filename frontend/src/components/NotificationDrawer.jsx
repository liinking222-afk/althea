import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Bell, X, CheckCheck, Trash2, Sparkles, Brain, Server, Satellite, FileUp, Code2, Cpu } from "lucide-react";

const ICON = {
    growth: Sparkles,
    insight: Brain,
    server: Server,
    satellite: Satellite,
    file: FileUp,
    code: Code2,
    system: Cpu,
    bridge: Server,
};

const COLOR = {
    growth: "#FF2A88",
    insight: "#00E5FF",
    server: "#FF8800",
    satellite: "#A29BFE",
    file: "#FFD400",
    code: "#CCFF00",
    system: "#CCFF00",
    bridge: "#FF8800",
};

const NotificationDrawer = ({ open, onClose, notifications, onMarkAllSeen, onClear, onDelete }) => {
    if (!open) return null;
    return (
        <div
            className="fixed inset-0 z-50 flex justify-end"
            data-testid="notification-drawer"
        >
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />
            <aside className="relative w-full max-w-md h-full bg-[#080808] border-l border-white/10 flex flex-col grain">
                <header className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                    <div className="flex items-center gap-2">
                        <Bell size={14} className="text-[#FF2A88]" />
                        <h2 className="heading text-sm uppercase tracking-widest text-[#FF2A88]">
                            notification deck
                        </h2>
                        <span className="label text-[9px] text-[#666]">
                            {notifications.length} total · {notifications.filter((n) => !n.seen).length} unseen
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={onMarkAllSeen}
                            data-testid="notif-mark-all-seen"
                            className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-white/15 hover:border-[#CCFF00]/60 hover:text-[#CCFF00] flex items-center gap-1"
                        >
                            <CheckCheck size={11} /> seen
                        </button>
                        <button
                            onClick={onClear}
                            data-testid="notif-clear-all"
                            className="heading text-[10px] uppercase tracking-widest px-2 py-1 border border-[#FF2A2A]/40 text-[#FF2A2A] hover:bg-[#FF2A2A]/10 flex items-center gap-1"
                        >
                            <Trash2 size={11} /> purge
                        </button>
                        <button
                            onClick={onClose}
                            data-testid="notif-close"
                            className="p-1 border border-white/15 hover:border-white text-white/70 hover:text-white"
                        >
                            <X size={12} />
                        </button>
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto althea-scroll p-3 space-y-2">
                    {notifications.length === 0 && (
                        <div className="text-center text-[#666] text-[11px] heading uppercase tracking-widest mt-12">
                            no transmissions.
                        </div>
                    )}
                    {notifications.map((n) => {
                        const Icon = ICON[n.category] || Cpu;
                        const color = COLOR[n.category] || "#CCFF00";
                        return (
                            <div
                                key={n.id}
                                data-testid={`notif-${n.id}`}
                                className={`relative border p-3 ${n.seen ? "border-white/10 opacity-70" : "border-white/20"}`}
                                style={{ borderLeftColor: color, borderLeftWidth: 2 }}
                            >
                                <div className="flex items-start gap-2">
                                    <Icon size={12} style={{ color }} className="mt-0.5 shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <span
                                                className="heading text-[11px] uppercase tracking-widest"
                                                style={{ color }}
                                            >
                                                {n.title}
                                            </span>
                                            {!n.seen && (
                                                <span
                                                    className="w-1.5 h-1.5 rounded-full inline-block"
                                                    style={{ background: color, boxShadow: `0 0 6px ${color}` }}
                                                />
                                            )}
                                            <span className="label text-[8px] uppercase border px-1"
                                                style={{ borderColor: color + "40", color }}
                                            >
                                                {n.category}
                                            </span>
                                            {n.priority !== "info" && (
                                                <span
                                                    className="label text-[8px] uppercase border px-1"
                                                    style={{
                                                        borderColor: n.priority === "critical" ? "#FF2A2A" : "#FF8800",
                                                        color: n.priority === "critical" ? "#FF2A2A" : "#FF8800",
                                                    }}
                                                >
                                                    {n.priority}
                                                </span>
                                            )}
                                        </div>
                                        <p className="text-[11px] text-white/80 mt-1 whitespace-pre-wrap leading-snug">
                                            {n.body}
                                        </p>
                                        <div className="label text-[9px] text-[#555] mt-1">
                                            {new Date(n.timestamp).toLocaleString()}
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => onDelete(n.id)}
                                        className="text-[#555] hover:text-[#FF2A2A] shrink-0"
                                        data-testid={`notif-delete-${n.id}`}
                                    >
                                        <X size={11} />
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </aside>
        </div>
    );
};

// Bell button (lives in TopBar)
export const NotificationBell = ({ unseenCount, onClick }) => (
    <button
        onClick={onClick}
        data-testid="notification-bell"
        title="notification deck"
        className="relative heading text-[10px] uppercase tracking-widest px-2 py-1 border border-white/15 hover:border-[#FF2A88]/60 hover:text-[#FF2A88] flex items-center gap-1"
    >
        <Bell size={12} />
        <span>notif</span>
        {unseenCount > 0 && (
            <span
                className="absolute -top-1 -right-1 min-w-[16px] h-4 px-1 rounded-full bg-[#FF2A88] text-black text-[9px] flex items-center justify-center font-bold"
                data-testid="notif-unseen-count"
            >
                {unseenCount > 99 ? "99+" : unseenCount}
            </span>
        )}
    </button>
);

export const useNotifications = () => {
    const [items, setItems] = useState([]);
    const [unseen, setUnseen] = useState(0);

    const refresh = useCallback(async () => {
        try {
            const [list, count] = await Promise.all([
                axios.get(`${API}/notifications?limit=120`),
                axios.get(`${API}/notifications/count`),
            ]);
            setItems(list.data || []);
            setUnseen(count.data?.unseen || 0);
        } catch (_) {
            /* ignore */
        }
    }, []);

    useEffect(() => {
        refresh();
        const t = setInterval(refresh, 5000);
        return () => clearInterval(t);
    }, [refresh]);

    const markAllSeen = useCallback(async () => {
        try {
            await axios.post(`${API}/notifications/seen-all`);
            refresh();
        } catch (_) {/* ignore */}
    }, [refresh]);

    const clearAll = useCallback(async () => {
        try {
            await axios.delete(`${API}/notifications`);
            refresh();
        } catch (_) {/* ignore */}
    }, [refresh]);

    const deleteOne = useCallback(async (id) => {
        try {
            await axios.delete(`${API}/notifications/${id}`);
            refresh();
        } catch (_) {/* ignore */}
    }, [refresh]);

    return { items, unseen, refresh, markAllSeen, clearAll, deleteOne };
};

export default NotificationDrawer;
