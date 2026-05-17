import React from "react";
import {
    Camera,
    Mic,
    MapPin,
    Bluetooth,
    Usb,
    Bell,
} from "lucide-react";

const ITEMS = [
    { key: "camera", label: "camera", Icon: Camera },
    { key: "microphone", label: "microphone", Icon: Mic },
    { key: "geolocation", label: "gps / geolocation", Icon: MapPin },
    { key: "bluetooth", label: "bluetooth", Icon: Bluetooth },
    { key: "usb", label: "web usb", Icon: Usb },
    { key: "notifications", label: "notifications", Icon: Bell },
];

const PermissionsPanel = ({ permissions, togglePermission }) => {
    return (
        <div
            className="panel cut p-4 grain relative"
            data-testid="permissions-panel"
        >
            <header className="flex items-center justify-between mb-3">
                <h3 className="heading text-sm tracking-widest uppercase">
                    device bridge
                </h3>
                <span className="label text-[9px]">
                    {Object.values(permissions).filter(Boolean).length}/6
                </span>
            </header>
            <ul className="space-y-2">
                {ITEMS.map(({ key, label, Icon }) => {
                    const on = permissions[key];
                    return (
                        <li
                            key={key}
                            className="flex items-center justify-between"
                        >
                            <div className="flex items-center gap-2">
                                <Icon
                                    size={14}
                                    className={
                                        on
                                            ? "text-[#CCFF00]"
                                            : "text-[#666]"
                                    }
                                />
                                <span
                                    className={`text-[11px] uppercase tracking-widest heading ${on ? "text-white" : "text-[#888]"}`}
                                >
                                    {label}
                                </span>
                            </div>
                            <input
                                type="checkbox"
                                className="althea-switch"
                                checked={on}
                                onChange={() => togglePermission(key)}
                                data-testid={`permission-toggle-${key}`}
                            />
                        </li>
                    );
                })}
            </ul>
            <div className="mt-3 text-[10px] text-[#666] leading-snug">
                althea requests host permissions on demand. revoke any time.
            </div>
        </div>
    );
};

export default PermissionsPanel;
