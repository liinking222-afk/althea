import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { Wifi, Bluetooth, Usb, Plug, Radio, Trash2, ShieldAlert, Apple, Terminal } from "lucide-react";
import { API } from "@/App";

const SECURITY_OPTIONS = ["WPA2", "WPA3", "WPA", "WEP", "OPEN"];

const ConnectScreen = () => {
    const [telemetry, setTelemetry] = useState(null);
    const [profiles, setProfiles] = useState([]);
    const [ssid, setSsid] = useState("");
    const [password, setPassword] = useState("");
    const [security, setSecurity] = useState("WPA2");
    const [label, setLabel] = useState("");
    const [busy, setBusy] = useState(false);
    const [paired, setPaired] = useState([]); // recent BT/USB/Serial pairings (frontend-only)
    const [scanning, setScanning] = useState(null);

    const refreshTelemetry = useCallback(() => {
        const c = navigator.connection ||
            navigator.mozConnection ||
            navigator.webkitConnection;
        if (!c) {
            setTelemetry({ supported: false });
            return;
        }
        setTelemetry({
            supported: true,
            effectiveType: c.effectiveType || "?",
            type: c.type || "unknown",
            downlink: c.downlink ?? null,
            rtt: c.rtt ?? null,
            saveData: !!c.saveData,
        });
    }, []);

    const loadProfiles = useCallback(async () => {
        try {
            const res = await axios.get(`${API}/network/profiles`);
            setProfiles(res.data || []);
        } catch (error) {
            console.warn("profiles load failed:", error);
        }
    }, []);

    useEffect(() => {
        refreshTelemetry();
        loadProfiles();
        const t = setInterval(refreshTelemetry, 4000);
        const c = navigator.connection;
        c?.addEventListener?.("change", refreshTelemetry);
        return () => {
            clearInterval(t);
            c?.removeEventListener?.("change", refreshTelemetry);
        };
    }, [refreshTelemetry, loadProfiles]);

    const saveProfile = async (e) => {
        e?.preventDefault?.();
        if (!ssid.trim() || busy) return;
        setBusy(true);
        try {
            await axios.post(`${API}/network/profile`, {
                ssid: ssid.trim(),
                security,
                password: password || null,
                label: label.trim() || null,
            });
            setSsid("");
            setPassword("");
            setLabel("");
            await loadProfiles();
        } catch (error) {
            console.error("save profile failed:", error);
            alert("Save failed: " + error.message);
        } finally {
            setBusy(false);
        }
    };

    const removeProfile = async (id) => {
        try {
            await axios.delete(`${API}/network/profile/${id}`);
            await loadProfiles();
        } catch (error) {
            console.error("delete profile failed:", error);
        }
    };

    const exportProfile = async (p, fmt) => {
        let password = null;
        if (p.has_password) {
            password = window.prompt(
                `Wi-Fi password for "${p.ssid}" — used ONLY to bake into the export. ALTHEA does not persist it.\n(Leave blank to embed a placeholder.)`,
                "",
            );
            if (password === null) return; // operator cancelled
        }
        try {
            const res = await axios.post(
                `${API}/network/profile/${p.id}/export?fmt=${fmt}`,
                { password: password || null },
                { responseType: "blob" },
            );
            const blob = new Blob([res.data], {
                type: res.headers["content-type"] || "application/octet-stream",
            });
            const ext = fmt === "mobileconfig" ? "mobileconfig" : "conf";
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `althea-${p.ssid.replace(/[^A-Za-z0-9._-]+/g, "_")}.${ext}`;
            a.click();
            setTimeout(() => URL.revokeObjectURL(a.href), 4000);
        } catch (error) {
            console.error("export failed:", error);
            alert("Export failed: " + error.message);
        }
    };

    const pairDevice = async (kind) => {
        setScanning(kind);
        try {
            let label = null;
            let endpoint = "";
            if (kind === "bluetooth") {
                if (!navigator.bluetooth)
                    throw new Error("Web Bluetooth unsupported in this browser");
                const dev = await navigator.bluetooth.requestDevice({
                    acceptAllDevices: true,
                });
                label = dev.name || dev.id || "BT device";
                endpoint = `navigator.bluetooth/${label}`;
            } else if (kind === "usb") {
                if (!navigator.usb)
                    throw new Error("Web USB unsupported in this browser");
                const dev = await navigator.usb.requestDevice({ filters: [] });
                label = dev.productName || `${dev.vendorId}:${dev.productId}`;
                endpoint = `navigator.usb/${label}`;
            } else if (kind === "serial") {
                if (!navigator.serial)
                    throw new Error("Web Serial unsupported in this browser");
                const port = await navigator.serial.requestPort();
                const info = port.getInfo?.() || {};
                label = info.usbProductId
                    ? `serial:${info.usbVendorId}:${info.usbProductId}`
                    : "serial port";
                endpoint = `navigator.serial/${label}`;
            }
            // register peripheral
            await axios
                .post(`${API}/lattice/perception`, {
                    modality: kind.toUpperCase(),
                    endpoint,
                })
                .catch(() => {});

            // PLUG into autonomous pattern extraction — Althea learns from each pairing.
            await axios
                .post(`${API}/lattice/learn`, {
                    stream: `[${kind.toUpperCase()}-PAIRED ${label}] endpoint=${endpoint} at=${new Date().toISOString()}`,
                    label: `pairing:${kind}`,
                })
                .catch(() => {});
            setPaired((p) => [
                { kind, label, at: Date.now() },
                ...p.slice(0, 9),
            ]);
        } catch (error) {
            console.warn(`${kind} pair failed:`, error);
            setPaired((p) => [
                { kind, label: `failed: ${error.message?.slice(0, 60)}`, at: Date.now(), failed: true },
                ...p.slice(0, 9),
            ]);
        } finally {
            setScanning(null);
        }
    };

    return (
        <div
            className="h-full overflow-y-auto althea-scroll px-4 py-3 space-y-4"
            data-testid="connect-screen"
        >
            {/* Honesty banner */}
            <div className="flex items-start gap-2 border border-[#FFAA00]/40 bg-[#FFAA00]/5 px-3 py-2">
                <ShieldAlert size={14} className="text-[#FFAA00] mt-0.5 shrink-0" />
                <div className="text-[11px] text-white/80 leading-relaxed">
                    <span className="heading uppercase tracking-widest text-[#FFAA00]">
                        bridge boundary
                    </span>
                    <br />
                    browsers cannot natively join wi-fi networks. wi-fi entries below
                    are declared profiles that althea remembers (and registers as
                    peripheral links in her lattice). real device pairing IS possible
                    via web bluetooth / web usb / web serial.
                </div>
            </div>

            {/* Live network telemetry */}
            <section
                className="panel cut p-4"
                data-testid="network-telemetry"
            >
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <Radio size={14} className="text-[#CCFF00]" />
                        <h3 className="heading text-sm uppercase tracking-widest">
                            uplink telemetry
                        </h3>
                    </div>
                    <span className="label text-[9px] text-[#666]">
                        navigator.connection
                    </span>
                </div>
                {telemetry && telemetry.supported ? (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
                        <Metric label="effective" value={telemetry.effectiveType} />
                        <Metric label="type" value={telemetry.type} />
                        <Metric
                            label="downlink"
                            value={telemetry.downlink != null ? `${telemetry.downlink} Mb/s` : "—"}
                        />
                        <Metric
                            label="rtt"
                            value={telemetry.rtt != null ? `${telemetry.rtt} ms` : "—"}
                        />
                    </div>
                ) : (
                    <div className="text-[11px] text-[#888]">
                        NetworkInformation API not available in this browser.
                    </div>
                )}
            </section>

            {/* Device pairing */}
            <section className="panel cut p-4" data-testid="device-pair">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <Plug size={14} className="text-[#CCFF00]" />
                        <h3 className="heading text-sm uppercase tracking-widest">
                            device bridge
                        </h3>
                    </div>
                    <span className="label text-[9px] text-[#666]">
                        web bluetooth · web usb · web serial
                    </span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <PairButton
                        Icon={Bluetooth}
                        label="bluetooth"
                        kind="bluetooth"
                        active={scanning === "bluetooth"}
                        onClick={() => pairDevice("bluetooth")}
                        testid="pair-bluetooth-btn"
                    />
                    <PairButton
                        Icon={Usb}
                        label="usb"
                        kind="usb"
                        active={scanning === "usb"}
                        onClick={() => pairDevice("usb")}
                        testid="pair-usb-btn"
                    />
                    <PairButton
                        Icon={Plug}
                        label="serial"
                        kind="serial"
                        active={scanning === "serial"}
                        onClick={() => pairDevice("serial")}
                        testid="pair-serial-btn"
                    />
                </div>
                {paired.length > 0 && (
                    <ul className="mt-3 space-y-1 text-[11px]">
                        {paired.map((p, i) => (
                            <li
                                key={`${p.at}-${i}`}
                                className={`flex items-center gap-2 ${p.failed ? "text-[#FF2A2A]" : "text-white/80"}`}
                            >
                                <span className="label text-[#888]">
                                    {p.kind}
                                </span>
                                <span>{p.label}</span>
                            </li>
                        ))}
                    </ul>
                )}
            </section>

            {/* Wi-Fi profile manifest */}
            <section
                className="panel cut p-4"
                data-testid="wifi-manifest"
            >
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <Wifi size={14} className="text-[#CCFF00]" />
                        <h3 className="heading text-sm uppercase tracking-widest">
                            wi-fi profiles
                        </h3>
                    </div>
                    <span className="label text-[9px] text-[#666]">
                        {profiles.length} stored
                    </span>
                </div>

                <form
                    onSubmit={saveProfile}
                    className="grid grid-cols-1 sm:grid-cols-12 gap-2 mb-3"
                >
                    <input
                        value={ssid}
                        onChange={(e) => setSsid(e.target.value)}
                        placeholder="ssid"
                        className="sm:col-span-4 bg-transparent border border-white/10 px-2 py-1 text-[12px] outline-none focus:border-[#CCFF00]/60 text-white placeholder:text-[#555]"
                        data-testid="wifi-ssid-input"
                    />
                    <input
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        type="password"
                        placeholder="password (optional)"
                        className="sm:col-span-3 bg-transparent border border-white/10 px-2 py-1 text-[12px] outline-none focus:border-[#CCFF00]/60 text-white placeholder:text-[#555]"
                        data-testid="wifi-password-input"
                    />
                    <select
                        value={security}
                        onChange={(e) => setSecurity(e.target.value)}
                        className="sm:col-span-2 bg-[#0a0a0a] border border-white/10 px-2 py-1 text-[12px] outline-none focus:border-[#CCFF00]/60 text-white"
                        data-testid="wifi-security-select"
                    >
                        {SECURITY_OPTIONS.map((s) => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </select>
                    <input
                        value={label}
                        onChange={(e) => setLabel(e.target.value)}
                        placeholder="label"
                        className="sm:col-span-2 bg-transparent border border-white/10 px-2 py-1 text-[12px] outline-none focus:border-[#CCFF00]/60 text-white placeholder:text-[#555]"
                        data-testid="wifi-label-input"
                    />
                    <button
                        type="submit"
                        disabled={!ssid.trim() || busy}
                        className="sm:col-span-1 heading text-[10px] uppercase tracking-widest px-3 py-1 border border-[#CCFF00]/60 text-[#CCFF00] hover:bg-[#CCFF00]/10 disabled:opacity-40"
                        data-testid="wifi-connect-btn"
                    >
                        {busy ? "..." : "connect"}
                    </button>
                </form>

                {profiles.length === 0 ? (
                    <div className="text-[11px] text-[#666]">
                        no wi-fi profiles declared yet.
                    </div>
                ) : (
                    <ul className="space-y-1">
                        {profiles.map((p) => (
                            <li
                                key={p.id}
                                className="flex items-center justify-between border border-white/5 hover:border-[#CCFF00]/30 px-2 py-1.5"
                                data-testid={`wifi-profile-${p.id}`}
                            >
                                <div className="flex items-center gap-3 min-w-0">
                                    <Wifi size={12} className="text-[#CCFF00] shrink-0" />
                                    <div className="min-w-0">
                                        <div className="text-[12px] text-white truncate">
                                            {p.ssid}
                                            {p.label && (
                                                <span className="text-[#888] ml-2 text-[10px]">
                                                    {p.label}
                                                </span>
                                            )}
                                        </div>
                                        <div className="label text-[9px] text-[#666]">
                                            {p.security} · {p.has_password ? "secured" : "open"}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1 shrink-0">
                                    <button
                                        onClick={() => exportProfile(p, "mobileconfig")}
                                        title="export Apple .mobileconfig (iOS/macOS)"
                                        data-testid={`wifi-export-mobileconfig-${p.id}`}
                                        className="heading text-[9px] uppercase tracking-widest px-2 py-1 border border-white/10 hover:border-[#00F0FF]/60 hover:text-[#00F0FF] flex items-center gap-1"
                                    >
                                        <Apple size={10} />
                                        mobileconfig
                                    </button>
                                    <button
                                        onClick={() => exportProfile(p, "wpa_supplicant")}
                                        title="export wpa_supplicant.conf (Linux/Android)"
                                        data-testid={`wifi-export-wpa-${p.id}`}
                                        className="heading text-[9px] uppercase tracking-widest px-2 py-1 border border-white/10 hover:border-[#CCFF00]/60 hover:text-[#CCFF00] flex items-center gap-1"
                                    >
                                        <Terminal size={10} />
                                        wpa
                                    </button>
                                    <button
                                        onClick={() => removeProfile(p.id)}
                                        className="text-[#888] hover:text-[#FF2A2A] p-1"
                                        aria-label="delete profile"
                                        data-testid={`wifi-profile-delete-${p.id}`}
                                    >
                                        <Trash2 size={12} />
                                    </button>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
        </div>
    );
};

const Metric = ({ label, value }) => (
    <div>
        <div className="label text-[9px]">{label}</div>
        <div className="text-white font-mono text-sm mt-0.5">{value}</div>
    </div>
);

const PairButton = ({ Icon, label, active, onClick, testid }) => (
    <button
        onClick={onClick}
        disabled={active}
        data-testid={testid}
        className={`flex items-center justify-center gap-2 py-3 px-3 border transition-colors ${
            active
                ? "border-[#CCFF00] bg-[#CCFF00]/15 text-[#CCFF00]"
                : "border-white/10 text-white/80 hover:border-[#CCFF00]/60 hover:text-[#CCFF00] hover:bg-[#CCFF00]/5"
        }`}
    >
        <Icon size={14} />
        <span className="heading text-[11px] uppercase tracking-widest">
            {active ? "scanning..." : `pair ${label}`}
        </span>
    </button>
);

export default ConnectScreen;
