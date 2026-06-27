"use client";

import { useEffect, useRef } from "react";

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
  const mapRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);

  useEffect(() => {
    if (typeof window === "undefined" || !containerRef.current) return;
    if (mapRef.current) return; // already initialized

    import("leaflet").then((L) => {
      // Fix default icon path issue with webpack
      // @ts-expect-error leaflet icon workaround
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      const map = L.map(containerRef.current!, {
        center: [41.8781, -87.6298],
        zoom: 11,
        zoomControl: true,
        attributionControl: false,
      });

      // CartoDB Dark Matter tiles
      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        subdomains: "abcd",
        maxZoom: 19,
      }).addTo(map);

      L.control.attribution({
        prefix: false,
        position: "bottomright",
      }).addAttribution('© <a href="https://carto.com">CARTO</a> · <a href="https://data.cityofchicago.org">City of Chicago</a>').addTo(map);

      mapRef.current = map;
    });

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Fly to focused marker
  useEffect(() => {
    if (!mapRef.current || !focusMarker) return;
    mapRef.current.flyTo([focusMarker.lat, focusMarker.lng], 15, { duration: 1.2 });
  }, [focusMarker]);

  // Update markers when data changes
  useEffect(() => {
    if (!mapRef.current) return;

    import("leaflet").then((L) => {
      // Clear existing markers
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];

      if (markers.length === 0) return;

      const validMarkers = markers.filter((m) => m.lat && m.lng && !isNaN(m.lat) && !isNaN(m.lng));
      if (validMarkers.length === 0) return;

      validMarkers.forEach((m) => {
        const color = m.bucket === "high" ? "#e8293a" : m.bucket === "medium" ? "#f5a623" : "#1a8a50";
        const icon = L.divIcon({
          className: "",
          html: `<div style="
            width:12px;height:12px;border-radius:50%;
            background:${color};
            border:2px solid rgba(255,255,255,0.3);
            box-shadow:0 0 8px ${color}88;
          "></div>`,
          iconSize: [12, 12],
          iconAnchor: [6, 6],
        });

        const marker = L.marker([m.lat, m.lng], { icon })
          .bindPopup(`
            <div style="font-family:'IBM Plex Mono',monospace;background:#0a1220;color:#c4d4e8;padding:8px 12px;border-radius:4px;border:1px solid rgba(255,255,255,0.08);min-width:180px">
              <div style="font-size:11px;font-weight:700;color:${color};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">${(m.score * 100).toFixed(0)}% · ${m.bucket.toUpperCase()}</div>
              <div style="font-size:12px;font-weight:600;color:#fff;margin-bottom:3px">${m.name}</div>
              ${m.address ? `<div style="font-size:10px;color:rgba(196,212,232,0.4)">${m.address}</div>` : ""}
            </div>
          `, {
            className: "leaflet-popup-dark",
          })
          .addTo(mapRef.current!);

        markersRef.current.push(marker);
      });

      // Fit map to markers
      if (validMarkers.length === 1) {
        mapRef.current!.setView([validMarkers[0].lat, validMarkers[0].lng], 14);
      } else {
        const bounds = L.latLngBounds(validMarkers.map((m) => [m.lat, m.lng]));
        mapRef.current!.fitBounds(bounds, { padding: [40, 40] });
      }
    });
  }, [markers]);

  return (
    <>
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      />
      <style>{`
        .leaflet-popup-content-wrapper {
          background: transparent !important;
          box-shadow: none !important;
          padding: 0 !important;
        }
        .leaflet-popup-content {
          margin: 0 !important;
        }
        .leaflet-popup-tip-container { display: none; }
        .leaflet-control-attribution {
          background: rgba(6,11,17,0.7) !important;
          color: rgba(196,212,232,0.2) !important;
          font-size: 9px !important;
          font-family: 'IBM Plex Mono', monospace !important;
        }
        .leaflet-control-attribution a { color: rgba(196,212,232,0.3) !important; }
        .leaflet-bar a {
          background: #0d1824 !important;
          color: #c4d4e8 !important;
          border-color: rgba(255,255,255,0.08) !important;
        }
        .leaflet-bar a:hover { background: #162030 !important; }
      `}</style>
      <div
        ref={containerRef}
        style={{ height, width: "100%" }}
        className="rounded-md overflow-hidden border border-white/8"
      />
    </>
  );
}
