import React, { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import html2canvas from "html2canvas";
import { Eye, EyeOff } from "lucide-react";
import { API } from "@/App";

/**
 * Self-observation: Althea screenshots her own UI every N seconds and ships
 * the frame to /api/perception/frame. Cross-origin iframe capture is impossible
 * by browser policy — only Althea's own DOM is captured.
 */
const VisualPerception = ({ uiState }) => {
    const [enabled, setEnabled] = useState(() => {
        return localStorage.getItem("althea_vision") === "1";
    });
    const [latest, setLatest] = useState(null);
    const [busy, setBusy] = useState(false);
    const tickRef = useRef(null);
    const uiStateRef = useRef(uiState);

    useEffect(() => {
        uiStateRef.current = uiState;
    }, [uiState]);

    useEffect(() => {
        localStorage.setItem("althea_vision", enabled ? "1" : "0");
    }, [enabled]);

    const capture = useCallback(async () => {
        if (busy) return;
        const root = document.getElementById("althea-container");
        if (!root) return;
        setBusy(true);
        try {
            const canvas = await html2canvas(root, {
                useCORS: true,
                allowTaint: false,
                logging: false,
                scale: 0.4, // keep payload small
                backgroundColor: "#050505",
                ignoreElements: (el) =>
                    el.dataset?.testid === "althea-vision-pip",
            });
            const dataUrl = canvas.toDataURL("image/jpeg", 0.55);
            const res = await axios.post(`${API}/perception/frame`, {
                image_data: dataUrl,
                source: "self",
                width: canvas.width,
                height: canvas.height,
                ui_state: uiStateRef.current || {},
            });
            setLatest({
                src: dataUrl,
                node_id: res.data.node_id,
                size: res.data.size_bytes,
                at: Date.now(),
            });
        } catch (error) {
            console.warn("self-vision capture failed:", error);
        } finally {
            setBusy(false);
        }
    }, [busy]);

    useEffect(() => {
        if (!enabled) {
            if (tickRef.current) clearInterval(tickRef.current);
            tickRef.current = null;
            return;
        }
        capture();
        tickRef.current = setInterval(capture, 10000);
        return () => {
            if (tickRef.current) clearInterval(tickRef.current);
            tickRef.current = null;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [enabled]);

    return (
        <>
            <button
                onClick={() => setEnabled((v) => !v)}
                data-testid="vision-toggle"
                title={
                    enabled
                        ? "self-vision capturing every 10s"
                        : "enable self-observation"
                }
                className={`heading text-[10px] uppercase tracking-widest px-2 py-1 border flex items-center gap-1 ${
                    enabled
                        ? "border-[#CCFF00]/60 text-[#CCFF00] bg-[#CCFF00]/10"
                        : "border-white/15 text-[#888] hover:text-white"
                }`}
            >
                {enabled ? <Eye size={11} /> : <EyeOff size={11} />}
                {enabled ? "vision" : "vision off"}
            </button>

            {enabled && latest && (
                <div
                    className="fixed bottom-12 right-3 z-40 pointer-events-none"
                    data-testid="althea-vision-pip"
                >
                    <div className="relative">
                        <img
                            src={latest.src}
                            alt="self"
                            className="w-44 border-2 border-[#CCFF00]/40 shadow-[0_0_20px_rgba(204,255,0,0.25)]"
                        />
                        <div className="absolute -top-4 left-0 label text-[#CCFF00] glow text-[9px]">
                            self-vision · {latest.node_id}
                        </div>
                        {busy && (
                            <div className="absolute top-1 right-1 dot" />
                        )}
                    </div>
                </div>
            )}
        </>
    );
};

export default VisualPerception;
