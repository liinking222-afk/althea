import { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import { API } from "@/lib/auth";

/** Live feed for one direct-message room (human chat + shared Althea thread). */
export const useRoomFeed = (roomId) => {
    const [messages, setMessages] = useState([]);
    const [info, setInfo] = useState(null);
    const [asking, setAsking] = useState(false);
    const lastTs = useRef(null);

    const merge = useCallback((incoming) => {
        if (!incoming?.length) return;
        setMessages((prev) => {
            const seen = new Set(prev.map((m) => m.id));
            const next = [...prev, ...incoming.filter((m) => !seen.has(m.id))];
            next.sort((a, b) => (a.timestamp < b.timestamp ? -1 : 1));
            lastTs.current = next[next.length - 1]?.timestamp || lastTs.current;
            return next;
        });
    }, []);

    useEffect(() => {
        if (!roomId) return undefined;
        let alive = true;
        setMessages([]);
        lastTs.current = null;
        axios.get(`${API}/dm/${roomId}`).then((r) => alive && setInfo(r.data)).catch(() => {});
        const poll = async () => {
            try {
                const res = await axios.get(`${API}/dm/${roomId}/messages`, {
                    params: lastTs.current ? { since: lastTs.current } : { limit: 120 },
                });
                if (alive) merge(res.data);
            } catch { /* keep polling */ }
        };
        poll();
        const t = setInterval(poll, 2500);
        return () => { alive = false; clearInterval(t); };
    }, [roomId, merge]);

    const sendHuman = useCallback(async (content) => {
        const res = await axios.post(`${API}/dm/${roomId}/messages`, { content });
        merge([res.data]);
    }, [roomId, merge]);

    const askAlthea = useCallback(async (content) => {
        setAsking(true);
        try {
            const res = await axios.post(`${API}/dm/${roomId}/althea`, { content });
            merge([res.data.ask, res.data.reply].filter(Boolean));
        } finally {
            setAsking(false);
        }
    }, [roomId, merge]);

    return { messages, info, sendHuman, askAlthea, asking };
};
