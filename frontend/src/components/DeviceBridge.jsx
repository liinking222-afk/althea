// DeviceBridge — connects Althea to the phone's REAL hardware through the
// permitted mobile web APIs, plus install + 0-token "unrestrained" mode.
// Everything here is permission-based and honest: no hidden OS access.
import React, { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import { API } from "@/App";
import {
    Smartphone, MapPin, BatteryCharging, Compass, Bell, Mic, Camera,
    Download, Zap, Wifi, Vibrate,
} from "lucide-react";

const setDevice = (patch) => {
    if (typeof window === "undefined") return;
    window.__althea_device = { ...(window.__althea_device || {}), ...patch };
};

const Row = ({ icon: Icon, title, sub, children, testid }) => (
    <div className="border border-white/10 p-3" data-testid={testid}>
        <div className="flex items-center gap-2 mb-2">
            <Icon size={13} className="text-[#CCFF00]" />
            <span className="heading text-[11px] uppercase tracking-widest">{title}</span>
            {sub && <span className="label text-[9px] text-[#666] ml-auto">{sub}</span>}
        </div>
        {children}
    </div>
);

const Btn = ({ onClick, active, children, testid, tone = "lime" }) => {
    const tones = {
        lime: "border-[#CCFF00]/50 text-[#CCFF00] hover:bg-[#CCFF00]/10",
        cyan: "border-[#00E5FF]/50 text-[#00E5FF] hover:bg-[#00E5FF]/10",
        magenta: "border-[#FF2A88]/50 text-[#FF2A88] hover:bg-[#FF2A88]/10",
    };
    return (
        <button
            onClick={onClick}
            data-testid={testid}
            className={`heading text-[10px] uppercase tracking-widest px-3 py-1.5 border ${
                active ? tones[tone].replace("hover:", "") + " bg-white/5" : tones[tone]
            }`}
        >
            {children}
        </button>
    );
};

export const DeviceBridge = ({ sessionId }) => {
    const [installable, setInstallable] = useState(!!window.__althea_install);
    const [installed, setInstalled] = useState(
        window.matchMedia?.("(display-mode: standalone)")?.matches || false);
    const [mode, setMode] = useState("hybrid");
    const [geo, setGeo] = useState(null);
    const [battery, setBattery] = useState(null);
    const [net, setNet] = useState(null);
    const [motion, setMotion] = useState(null);
    const [notif, setNotif] = useState(
        typeof Notification !== "undefined" ? Notification.permission : "unsupported");
    const [listening, setListening] = useState(false);
    const [voiceText, setVoiceText] = useState("");
    const [camOn, setCamOn] = useState(false);
    const geoWatch = useRef(null);
    const recRef = useRef(null);
    const videoRef = useRef(null);
    const streamRef = useRef(null);
    const canvasRef = useRef(null);

    useEffect(() => {
        if (sessionId) {
            axios.get(`${API}/chat/mode/${sessionId}`)
                .then((r) => setMode(r.data.mode)).catch(() => {});
        }
        const onInstallable = () => setInstallable(true);
        window.addEventListener("althea:installable", onInstallable);
        return () => window.removeEventListener("althea:installable", onInstallable);
    }, [sessionId]);

    // platform fingerprint (honest, non-invasive)
    useEffect(() => {
        setDevice({
            platform: navigator.platform,
            ua_mobile: /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent),
            cores: navigator.hardwareConcurrency || null,
            lang: navigator.language,
        });
    }, []);

    const install = async () => {
        const evt = window.__althea_install;
        if (!evt) return;
        evt.prompt();
        const { outcome } = await evt.userChoice;
        if (outcome === "accepted") setInstalled(true);
        window.__althea_install = null;
        setInstallable(false);
    };

    const toggleMode = async () => {
        const next = mode === "direct" ? "hybrid" : "direct";
        await axios.post(`${API}/chat/mode`, { session_id: sessionId, mode: next });
        setMode(next);
        window.dispatchEvent(new CustomEvent("althea:mode", { detail: { mode: next } }));
    };

    useEffect(() => {
        const h = (e) => e.detail?.mode && setMode(e.detail.mode);
        window.addEventListener("althea:mode", h);
        return () => window.removeEventListener("althea:mode", h);
    }, []);

    const startGeo = () => {
        if (!navigator.geolocation) return;
        geoWatch.current = navigator.geolocation.watchPosition(
            (p) => {
                const g = {
                    lat: p.coords.latitude, lon: p.coords.longitude,
                    accuracy: Math.round(p.coords.accuracy),
                    speed: p.coords.speed,
                };
                setGeo(g);
                setDevice({ geo: g });
            },
            () => setGeo({ error: "denied" }),
            { enableHighAccuracy: true, maximumAge: 10000, timeout: 15000 },
        );
    };
    useEffect(() => () => {
        if (geoWatch.current != null) navigator.geolocation.clearWatch(geoWatch.current);
    }, []);

    const readBattery = async () => {
        if (!navigator.getBattery) { setBattery({ error: "unsupported" }); return; }
        const b = await navigator.getBattery();
        const upd = () => {
            const v = { level: Math.round(b.level * 100), charging: b.charging };
            setBattery(v);
            setDevice({ battery: `${v.level}%${v.charging ? " charging" : ""}` });
        };
        upd();
        b.addEventListener("levelchange", upd);
        b.addEventListener("chargingchange", upd);
    };

    const readNet = useCallback(() => {
        const c = navigator.connection || navigator.webkitConnection;
        if (!c) { setNet({ error: "unsupported" }); return; }
        const v = { type: c.effectiveType, downlink: c.downlink, rtt: c.rtt };
        setNet(v);
        setDevice({ network: `${v.type} ${v.downlink ?? "?"}Mb/s ${v.rtt ?? "?"}ms` });
    }, []);
    useEffect(() => { readNet(); }, [readNet]);

    const startMotion = async () => {
        try {
            if (typeof DeviceOrientationEvent !== "undefined" &&
                typeof DeviceOrientationEvent.requestPermission === "function") {
                const res = await DeviceOrientationEvent.requestPermission();
                if (res !== "granted") { setMotion({ error: "denied" }); return; }
            }
            window.addEventListener("deviceorientation", (e) => {
                const m = {
                    tilt_fb: Math.round(e.beta || 0),
                    tilt_lr: Math.round(e.gamma || 0),
                    compass: Math.round(e.alpha || 0),
                };
                setMotion(m);
                setDevice({ orientation: m });
            });
        } catch {
            setMotion({ error: "unsupported" });
        }
    };

    const enableNotif = async () => {
        if (typeof Notification === "undefined") return;
        const p = await Notification.requestPermission();
        setNotif(p);
        if (p === "granted") {
            new Notification("ALTHEA online", {
                body: "I can now reach you on this device.",
                icon: "/icons/althea-192.png",
            });
        }
    };

    const vibrate = () => navigator.vibrate?.([60, 40, 120]);

    const toggleVoice = () => {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) { setVoiceText("speech recognition unsupported here"); return; }
        if (listening) {
            recRef.current?.stop();
            setListening(false);
            return;
        }
        const rec = new SR();
        rec.lang = "en-US";
        rec.interimResults = true;
        rec.continuous = false;
        rec.onresult = (e) => {
            const t = Array.from(e.results).map((r) => r[0].transcript).join("");
            setVoiceText(t);
            if (e.results[e.results.length - 1].isFinal) {
                window.dispatchEvent(new CustomEvent("althea:voice", { detail: { text: t } }));
            }
        };
        rec.onend = () => setListening(false);
        rec.onerror = () => setListening(false);
        recRef.current = rec;
        rec.start();
        setListening(true);
    };

    const toggleCam = async () => {
        if (camOn) {
            streamRef.current?.getTracks().forEach((t) => t.stop());
            streamRef.current = null;
            setCamOn(false);
            return;
        }
        try {
            const s = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: "environment" }, audio: false,
            });
            streamRef.current = s;
            if (videoRef.current) videoRef.current.srcObject = s;
            setCamOn(true);
            setDevice({ camera: "active" });
        } catch {
            setCamOn(false);
        }
    };
    useEffect(() => () => streamRef.current?.getTracks().forEach((t) => t.stop()), []);

    const snapshot = () => {
        const v = videoRef.current, c = canvasRef.current;
        if (!v || !c) return;
        c.width = v.videoWidth || 640;
        c.height = v.videoHeight || 480;
        c.getContext("2d").drawImage(v, 0, 0, c.width, c.height);
        c.toBlob((b) => {
            if (!b) return;
            const a = document.createElement("a");
            a.href = URL.createObjectURL(b);
            a.download = `althea-snapshot-${Date.now()}.jpg`;
            a.click();
            setTimeout(() => URL.revokeObjectURL(a.href), 4000);
        }, "image/jpeg", 0.85);
    };

    return (
        <section className="panel cut p-4 space-y-3" data-testid="device-bridge-phone">
            <div className="flex items-center gap-2">
                <Smartphone size={15} className="text-[#CCFF00]" />
                <h3 className="heading text-sm uppercase tracking-widest">phone bridge</h3>
                <span className="label text-[9px] text-[#666] ml-auto">
                    {installed ? "installed app" : "browser"} · permission-based
                </span>
            </div>

            <div className="text-[10px] text-white/60 leading-relaxed border border-[#00E5FF]/25 bg-[#00E5FF]/5 px-2 py-1.5">
                Althea binds to your phone's real hardware through granted permissions.
                Browsers sandbox apps — she cannot read SMS/other apps or run truly
                unlimited in the background. Everything below is genuine and consent-based.
            </div>

            {/* install + unrestrained mode */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <Row icon={Download} title="install app" sub="PWA" testid="dev-install">
                    {installed ? (
                        <div className="text-[11px] text-[#CCFF00]">running as installed app ✓</div>
                    ) : installable ? (
                        <Btn onClick={install} testid="dev-install-btn">install althea on this device</Btn>
                    ) : (
                        <div className="text-[10px] text-white/50">
                            use your browser menu → "Add to Home Screen" to install.
                        </div>
                    )}
                </Row>
                <Row icon={Zap} title="unrestrained mode" sub="0 tokens" testid="dev-mode">
                    <div className="flex items-center gap-2">
                        <Btn onClick={toggleMode} active={mode === "direct"} testid="dev-mode-btn"
                            tone="lime">
                            {mode === "direct" ? "direct · 0-llm ON" : "enable 0-token"}
                        </Btn>
                        <span className="text-[10px] text-white/50">
                            {mode === "direct"
                                ? "answers live from the internet, zero credits"
                                : "hybrid (LLM + uplink)"}
                        </span>
                    </div>
                </Row>
            </div>

            {/* live sensors */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <Row icon={MapPin} title="location" sub="GPS" testid="dev-geo">
                    {geo && !geo.error ? (
                        <div className="text-[11px] font-mono text-white/80">
                            {geo.lat.toFixed(5)}, {geo.lon.toFixed(5)}
                            <span className="text-[#666]"> · ±{geo.accuracy}m</span>
                        </div>
                    ) : (
                        <Btn onClick={startGeo} testid="dev-geo-btn" tone="cyan">
                            {geo?.error ? "denied — retry" : "share my location"}
                        </Btn>
                    )}
                </Row>
                <Row icon={BatteryCharging} title="battery" testid="dev-battery">
                    {battery && !battery.error ? (
                        <div className="text-[11px] font-mono text-white/80">
                            {battery.level}% {battery.charging ? "· charging" : ""}
                        </div>
                    ) : (
                        <Btn onClick={readBattery} testid="dev-battery-btn" tone="cyan">read battery</Btn>
                    )}
                </Row>
                <Row icon={Compass} title="motion & orientation" sub="gyro" testid="dev-motion">
                    {motion && !motion.error ? (
                        <div className="text-[11px] font-mono text-white/80">
                            fb {motion.tilt_fb}° · lr {motion.tilt_lr}° · hdg {motion.compass}°
                        </div>
                    ) : (
                        <Btn onClick={startMotion} testid="dev-motion-btn" tone="cyan">
                            {motion?.error ? `${motion.error}` : "enable sensors"}
                        </Btn>
                    )}
                </Row>
                <Row icon={Wifi} title="network" testid="dev-net">
                    {net && !net.error ? (
                        <div className="text-[11px] font-mono text-white/80">
                            {net.type} · {net.downlink ?? "?"} Mb/s · {net.rtt ?? "?"} ms
                        </div>
                    ) : (
                        <div className="text-[10px] text-white/50">NetworkInformation unavailable</div>
                    )}
                </Row>
            </div>

            {/* voice control */}
            <Row icon={Mic} title="voice control" sub="speech → terminal" testid="dev-voice">
                <div className="flex items-center gap-2 flex-wrap">
                    <Btn onClick={toggleVoice} active={listening} testid="dev-voice-btn" tone="magenta">
                        {listening ? "listening… tap to stop" : "talk to althea"}
                    </Btn>
                    {voiceText && (
                        <span className="text-[11px] text-white/70 italic">"{voiceText}"</span>
                    )}
                </div>
            </Row>

            {/* notifications + haptics */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <Row icon={Bell} title="notifications" testid="dev-notif">
                    {notif === "granted" ? (
                        <div className="text-[11px] text-[#CCFF00]">enabled ✓ althea can alert you</div>
                    ) : (
                        <Btn onClick={enableNotif} testid="dev-notif-btn" tone="cyan">
                            {notif === "denied" ? "blocked in settings" : "allow alerts"}
                        </Btn>
                    )}
                </Row>
                <Row icon={Vibrate} title="haptics" testid="dev-haptic">
                    <Btn onClick={vibrate} testid="dev-haptic-btn" tone="cyan">buzz this device</Btn>
                </Row>
            </div>

            {/* camera */}
            <Row icon={Camera} title="camera" sub="rear lens" testid="dev-camera">
                <div className="flex items-center gap-2 flex-wrap">
                    <Btn onClick={toggleCam} active={camOn} testid="dev-camera-btn" tone="magenta">
                        {camOn ? "stop camera" : "open camera"}
                    </Btn>
                    {camOn && (
                        <Btn onClick={snapshot} testid="dev-snapshot-btn" tone="lime">snapshot</Btn>
                    )}
                </div>
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className={`mt-2 w-full max-w-[320px] border border-white/10 ${camOn ? "block" : "hidden"}`}
                    data-testid="dev-camera-feed"
                />
                <canvas ref={canvasRef} className="hidden" />
            </Row>
        </section>
    );
};

export default DeviceBridge;
