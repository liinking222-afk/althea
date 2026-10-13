import React, { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { API } from "@/lib/auth";
import { MessageSquare, Search, Radio } from "lucide-react";

const Avatar = ({ u, size = 26 }) => (
    u?.picture ? (
        <img src={u.picture} alt="" className="rounded-sm object-cover" style={{ width: size, height: size }} />
    ) : (
        <div
            className="heading text-[11px] text-black bg-[#CCFF00] flex items-center justify-center"
            style={{ width: size, height: size }}
        >
            {(u?.name || u?.handle || "?").slice(0, 1).toUpperCase()}
        </div>
    )
);

export const CommsPanel = ({ activeRoomId, onOpenRoom }) => {
    const [q, setQ] = useState("");
    const [people, setPeople] = useState([]);
    const [rooms, setRooms] = useState([]);

    const loadRooms = useCallback(async () => {
        try {
            const res = await axios.get(`${API}/dm/rooms`);
            setRooms(res.data || []);
        } catch { /* polling */ }
    }, []);

    useEffect(() => {
        loadRooms();
        const t = setInterval(loadRooms, 4000);
        return () => clearInterval(t);
    }, [loadRooms]);

    useEffect(() => {
        const t = setTimeout(async () => {
            try {
                const res = await axios.get(`${API}/users`, { params: { q } });
                setPeople(res.data || []);
            } catch { /* ignore */ }
        }, 200);
        return () => clearTimeout(t);
    }, [q]);

    const open = async (userId) => {
        const res = await axios.post(`${API}/dm/open`, { user_id: userId });
        await loadRooms();
        onOpenRoom?.(res.data.room_id, res.data.peer);
    };

    const roomPeerIds = new Set(rooms.map((r) => r.peer?.user_id));

    return (
        <div className="flex flex-col h-full" data-testid="comms-panel">
            <div className="flex items-center gap-2 mb-3">
                <Radio size={12} className="text-[#CCFF00]" />
                <span className="label text-[10px] uppercase tracking-widest text-[#CCFF00]">direct lines</span>
                <div className="flex-1" />
                <span className="label text-[9px] text-[#666]">{rooms.length} open</span>
            </div>

            <div className="space-y-1 mb-4" data-testid="comms-inbox">
                {rooms.length === 0 && (
                    <div className="text-[10px] text-[#666] font-mono leading-snug">
                        no conversations yet — find someone below and open a line. one shared althea joins every room.
                    </div>
                )}
                {rooms.map((r) => (
                    <button
                        key={r.room_id}
                        onClick={() => onOpenRoom?.(r.room_id, r.peer)}
                        data-testid={`comms-room-${r.room_id}`}
                        className={`w-full text-left flex items-center gap-2 px-2 py-1.5 border transition-colors ${
                            activeRoomId === r.room_id
                                ? "border-[#CCFF00]/60 bg-[#CCFF00]/5"
                                : "border-white/10 hover:border-white/30"
                        }`}
                    >
                        <Avatar u={r.peer} />
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-1.5">
                                <span className="heading text-[11px] uppercase tracking-wider text-white truncate">
                                    {r.peer?.name || "unknown"}
                                </span>
                                {r.peer?.online && <span className="w-1.5 h-1.5 rounded-full bg-[#48FFB0]" title="online" />}
                                {r.unread > 0 && (
                                    <span className="ml-auto text-[9px] font-mono bg-[#FF2A88] text-black px-1" data-testid={`comms-unread-${r.room_id}`}>
                                        {r.unread}
                                    </span>
                                )}
                            </div>
                            <div className="text-[9px] text-[#777] font-mono truncate">{r.last_message || "—"}</div>
                        </div>
                    </button>
                ))}
            </div>

            <div className="flex items-center gap-2 border border-white/15 px-2 py-1 mb-2 focus-within:border-[#CCFF00]/60">
                <Search size={11} className="text-[#666]" />
                <input
                    value={q}
                    onChange={(e) => setQ(e.target.value)}
                    placeholder="find people by name or @handle"
                    className="flex-1 bg-transparent text-[11px] font-mono outline-none"
                    data-testid="comms-search-input"
                />
            </div>
            <div className="flex-1 overflow-y-auto althea-scroll space-y-1" data-testid="comms-people">
                {people.filter((p) => !roomPeerIds.has(p.user_id) || q).map((p) => (
                    <button
                        key={p.user_id}
                        onClick={() => open(p.user_id)}
                        data-testid={`comms-user-${p.handle}`}
                        className="w-full text-left flex items-center gap-2 px-2 py-1.5 border border-white/5 hover:border-white/30 transition-colors group"
                    >
                        <Avatar u={p} size={22} />
                        <div className="flex-1 min-w-0">
                            <div className="text-[11px] text-white truncate">{p.name}</div>
                            <div className="text-[9px] text-[#666] font-mono">@{p.handle}{p.online ? " · online" : ""}</div>
                        </div>
                        <MessageSquare size={11} className="text-[#444] group-hover:text-[#CCFF00]" />
                    </button>
                ))}
                {people.length === 0 && (
                    <div className="text-[10px] text-[#555] font-mono">nobody else here yet.</div>
                )}
            </div>
        </div>
    );
};

export default CommsPanel;
