"use client";

import { useEffect, useRef, useState } from "react";

interface MarkerData {
  lat: number;
  lng: number;
  name: string;
  score: number;
  bucket: string;
  address?: string;
}

interface ChicagoMapProps {
  markers?: MarkerData[];
  focusMarker?: { lat: number; lng: number } | null;
  height?: string;
}

export function ChicagoMap({ markers = [], focusMarker, height = "400px" }: ChicagoMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mapRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const LRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const markersRef = useRef<any[]>([]);
  const [mapReady, setMapReady] = useState(false);

  // Initialize map once
  useEffect(() => {
    if (typeof window === "undefined" || !containerRef.current || mapRef.current) return;

    import("leaflet").then((L) => {
      if (mapRef.current) return; // guard double-init

      LRef.current = L;

      const map = L.map(containerRef.current!, {
        center: [41.8781, -87.6298],
        zoom: 11,
        zoomControl: true,
        attributionControl: false,
      });

      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        subdomains: "abcd",
        maxZoom: 19,
      }).addTo(map);

      L.control.attribution({ prefix: false, position: "bottomright" })
        .addAttribution('© <a href="https://carto.com">CARTO</a> · <a href="https://data.cityofchicago.org">City of Chicago</a>')
        .addTo(map);

      mapRef.current = map;
      setMapReady(true); // ← triggers marker effect once map is live
    });

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        setMapReady(false);
      }
    };
  }, []);

  // Smooth fly-to when a business is selected
  useEffect(() => {
    if (!mapReady || !mapRef.current || !focusMarker) return;
    mapRef.current.flyTo([focusMarker.lat, focusMarker.lng], 15, { duration: 1.2 });
  }, [focusMarker, mapReady]);

  // Re-render markers whenever data OR map-ready state changes
  useEffect(() => {
    if (!mapReady || !mapRef.current || !LRef.current) return;
    const L = LRef.current;

    // Clear old markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    const valid = markers.filter(
      (m) => typeof m.lat === "number" && typeof m.lng === "number" && !isNaN(m.lat) && !isNaN(m.lng)
    );
    if (valid.length === 0) return;

    valid.forEach((m) => {
      const color = m.bucket === "high" ? "#e8293a" : m.bucket === "medium" ? "#f5a623" : "#1a8a50";
      const icon = L.divIcon({
        className: "",
        html: `<div style="
          width:14px;height:14px;border-radius:50%;
          background:${color};
          border:2px solid rgba(255,255,255,0.35);
          box-shadow:0 0 10px ${color}99;
        "></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      const popup = `
        <div style="font-family:'IBM Plex Mono',monospace;background:#0a1220;color:#c4d4e8;padding:8px 12px;border-radius:4px;border:1px solid rgba(255,255,255,0.08);min-width:190px">
          <div style="font-size:11px;font-weight:700;color:${color};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">${(m.score * 100).toFixed(0)}% · ${m.bucket.toUpperCase()}</div>
          <div style="font-size:12px;font-weight:600;color:#fff;margin-bottom:3px">${m.name}</div>
          ${m.address ? `<div style="font-size:10px;color:rgba(196,212,232,0.35)">${m.address}</div>` : ""}
        </div>`;

      const marker = L.marker([m.lat, m.lng], { icon })
        .bindPopup(popup, { className: "leaflet-popup-dark" })
        .addTo(mapRef.current);

      markersRef.current.push(marker);
    });

    // Fit bounds or zoom to single marker
    if (valid.length === 1) {
      mapRef.current.setView([valid[0].lat, valid[0].lng], 15);
    } else {
      const bounds = L.latLngBounds(valid.map((m) => [m.lat, m.lng] as [number, number]));
      mapRef.current.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
    }
  }, [markers, mapReady]);

  return (
    <>
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <style>{`
        .leaflet-popup-content-wrapper { background:transparent!important; box-shadow:none!important; padding:0!important; }
        .leaflet-popup-content { margin:0!important; }
        .leaflet-popup-tip-container { display:none; }
        .leaflet-control-attribution { background:rgba(6,11,17,0.7)!important; color:rgba(196,212,232,0.2)!important; font-size:9px!important; font-family:'IBM Plex Mono',monospace!important; }
        .leaflet-control-attribution a { color:rgba(196,212,232,0.3)!important; }
        .leaflet-bar a { background:#0d1824!important; color:#c4d4e8!important; border-color:rgba(255,255,255,0.08)!important; }
        .leaflet-bar a:hover { background:#162030!important; }
      `}</style>
      <div
        ref={containerRef}
        style={{ height, width: "100%" }}
        className="rounded-md overflow-hidden border border-white/8"
      />
    </>
  );
}
