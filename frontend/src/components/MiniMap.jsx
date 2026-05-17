import React, { useEffect, useRef } from "react";
import L from "leaflet";

// Fix default icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const MiniMap = ({ geo }) => {
    const mapRef = useRef(null);
    const containerRef = useRef(null);
    const markerRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current || mapRef.current) return;
        const map = L.map(containerRef.current, {
            zoomControl: false,
            attributionControl: true,
            preferCanvas: true,
        }).setView([20, 0], 2);

        L.tileLayer(
            "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            {
                attribution: "© OpenStreetMap · CartoDB",
                maxZoom: 19,
                subdomains: "abcd",
            },
        ).addTo(map);

        L.control.zoom({ position: "bottomright" }).addTo(map);
        mapRef.current = map;

        return () => {
            map.remove();
            mapRef.current = null;
        };
    }, []);

    useEffect(() => {
        if (!mapRef.current) return;
        if (geo) {
            const ll = [geo.lat, geo.lon];
            mapRef.current.setView(ll, 13, { animate: true });

            if (markerRef.current) markerRef.current.remove();
            const accentIcon = L.divIcon({
                className: "althea-pin",
                html: `<div style="
                    width:14px;height:14px;border-radius:50%;
                    background:#CCFF00;box-shadow:0 0 14px #CCFF00;
                    border:2px solid #050505;"></div>`,
                iconSize: [14, 14],
                iconAnchor: [7, 7],
            });
            markerRef.current = L.marker(ll, { icon: accentIcon }).addTo(
                mapRef.current,
            );
            L.circle(ll, {
                radius: geo.acc,
                color: "#CCFF00",
                fillOpacity: 0.05,
                weight: 1,
            }).addTo(mapRef.current);
        }
    }, [geo]);

    return (
        <div
            ref={containerRef}
            className="absolute inset-0"
            data-testid="map-container"
        />
    );
};

export default MiniMap;
