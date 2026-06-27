"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import Link from "next/link";
import { Search, ArrowLeft } from "lucide-react";
import { Footer } from "@/components/footer";

const ChicagoMap = dynamic(
  () => import("@/components/ui/chicago-map").then((m) => m.ChicagoMap),
  { ssr: false, loading: () => <div className="h-64 rounded-md bg-white/[0.03] border border-white/8 animate-pulse" /> }
);

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Business {
  business_id: string;
  dba_name: string;
  risk_score: number;
  risk_bucket: string;
  days_since_last_inspection?: number;
  all_time_fail_rate?: number;
  all_time_violations_per_insp?: number;
  consecutive_fails?: number;
  result_trend?: number;
  address?: string;
  zip_code?: string;
  latitude?: number;
  longitude?: number;
}

function ScoreGauge({ score }: { score: number }) {
  const pct = score * 100;
  const r = 52;
  const circ = 2 * Math.PI * r;
  const stroke = circ * (1 - score);
  const color = score >= 0.66 ? "#e8293a" : score >= 0.33 ? "#f5a623" : "#1a8a50";
  const label = score >= 0.66 ? "HIGH" : score >= 0.33 ? "MEDIUM" : "LOW";

  return (
    <div className="flex flex-col items-center">
      <svg width="130" height="130" viewBox="0 0 130 130">
        <circle cx="65" cy="65" r={r} fill="none" stroke="#ffffff08" strokeWidth="8" />
        <circle
          cx="65" cy="65" r={r}
          fill="none" stroke={color} strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${circ}`}
          strokeDashoffset={stroke}
          transform="rotate(-90 65 65)"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
        <text x="65" y="60" textAnchor="middle" fill={color} fontSize="22" fontWeight="700" fontFamily="IBM Plex Mono">
          {pct.toFixed(0)}%
        </text>
        <text x="65" y="78" textAnchor="middle" fill={color} fontSize="9" fontWeight="600" fontFamily="IBM Plex Mono" letterSpacing="2">
          {label}
        </text>
      </svg>
    </div>
  );
}

function SearchPageInner() {
  const searchParams = useSearchParams();
  const [query, setQuery] = useState(searchParams.get("q") ?? "");
  const [results, setResults] = useState<Business[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<Business | null>(null);
  const [searched, setSearched] = useState(false);

  // Auto-run search when arriving from dashboard with ?q=
  useEffect(() => {
    const q = searchParams.get("q");
    if (q) doSearch(q);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function doSearch(q: string) {
    if (!q.trim()) return;
    setLoading(true); setSearched(true); setSelected(null);
    try {
      const res = await fetch(`${API}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, limit: 15 }),
      });
      setResults(await res.json());
    } catch { setResults([]); }
    finally { setLoading(false); }
  }

  const indicators = selected ? [
    { label: "Days since last inspection", value: selected.days_since_last_inspection != null ? `${selected.days_since_last_inspection} days` : "—" },
    { label: "All-time fail rate",         value: selected.all_time_fail_rate != null ? `${(selected.all_time_fail_rate*100).toFixed(0)}%` : "—" },
    { label: "Violations per inspection",  value: selected.all_time_violations_per_insp != null ? selected.all_time_violations_per_insp.toFixed(1) : "—" },
    { label: "Consecutive fails",          value: selected.consecutive_fails != null ? String(Math.round(selected.consecutive_fails)) : "0" },
    { label: "Result trend",               value: selected.result_trend != null ? (selected.result_trend < -0.00001 ? "↓ declining" : "→ stable") : "—" },
    { label: "Address",                    value: selected.address ?? "—" },
    { label: "ZIP",                        value: selected.zip_code ?? "—" },
  ] : [];

  return (
    <div className="min-h-screen bg-[#060b11] text-[#c4d4e8]">

      {/* Nav */}
      <nav className="sticky top-0 z-50 flex items-center justify-between px-8 h-13 border-b border-white/5 bg-[#060b11]/90 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="flex items-center gap-2 text-white/30 hover:text-white/60 transition-colors">
            <ArrowLeft size={14} />
            <span className="font-mono text-xs uppercase tracking-widest">Dashboard</span>
          </Link>
          <span className="text-white/10 px-2">|</span>
          <span className="font-mono text-xs text-white/30 uppercase tracking-widest">Business Search</span>
          <Link href="/about" className="font-mono text-xs uppercase tracking-widest text-white/30 hover:text-red-400 transition-colors ml-4">About</Link>
        </div>
        <Link href="/" className="flex items-center gap-2.5">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
          <span className="font-mono text-xs font-bold text-white/60 tracking-widest">CLOSURE RADAR</span>
          <span className="hidden sm:flex items-center gap-1 ml-0.5">
            {["✶","✶","✶","✶"].map((s, i) => (
              <span key={i} className="text-[#e8293a] text-[0.58rem] leading-none" style={{ textShadow: "0 0 5px rgba(232,41,58,0.5)" }}>{s}</span>
            ))}
          </span>
        </Link>
      </nav>

      <div className="max-w-5xl mx-auto px-8 py-12">
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <p className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-red-500">Business Lookup</p>
            <span className="font-mono text-[0.5rem] text-[#1F6CB0]/35 uppercase tracking-widest">312 · 77 Neighborhoods</span>
          </div>
          <h1 className="font-mono text-2xl font-bold text-white mb-2">Search Any Chicago Business</h1>
          <p className="text-white/30 text-sm">Enter a restaurant, café, or bookstore name to see its closure risk score and key indicators.</p>
        </div>

        {/* Search bar */}
        <div className="relative mb-8">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/25" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && doSearch(query)}
            placeholder="e.g. Metropolis Coffee · Book Cellar · Pilsen restaurant..."
            className="w-full bg-white/[0.03] border border-white/10 rounded-md pl-11 pr-32 py-3.5 font-mono text-sm text-white placeholder-white/20 outline-none focus:border-red-500/40 transition-colors"
          />
          <button
            onClick={() => doSearch(query)}
            className="absolute right-2 top-1/2 -translate-y-1/2 bg-red-500 hover:bg-red-600 text-white font-mono text-xs uppercase tracking-widest px-5 py-2 rounded transition-colors"
          >
            Search
          </button>
        </div>

        {/* Neighborhood quick-search */}
        <div className="flex flex-wrap items-center gap-2 mb-8">
          <span className="font-mono text-[0.55rem] uppercase tracking-widest text-white/15">Browse by neighborhood:</span>
          {["Wicker Park", "Logan Square", "Pilsen", "Hyde Park", "Lincoln Square", "River North", "Bridgeport"].map((n) => (
            <button
              key={n}
              onClick={() => { setQuery(n); doSearch(n); }}
              className="font-mono text-[0.58rem] uppercase tracking-widest px-2.5 py-1 rounded border border-white/8 text-white/25 hover:text-[#1F6CB0]/70 hover:border-[#1F6CB0]/20 transition-colors"
            >
              {n}
            </button>
          ))}
        </div>

        {/* Results + detail */}
        {searched && (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

            {/* Result list */}
            <div className="lg:col-span-2">
              <div className="font-mono text-[0.58rem] uppercase tracking-widest text-white/20 border-b border-white/5 pb-2 mb-3">
                {loading ? "Searching..." : `${results.length} result${results.length !== 1 ? "s" : ""}`}
              </div>

              {loading ? (
                <div className="space-y-2">{[...Array(5)].map((_, i) => <div key={i} className="h-14 rounded bg-white/[0.03] animate-pulse" />)}</div>
              ) : results.length === 0 ? (
                <p className="font-mono text-xs text-white/20 py-6">No businesses found. Try a partial name.</p>
              ) : (
                <div className="space-y-1.5">
                  {results.map((b) => {
                    const color = b.risk_bucket === "high" ? "text-red-400 border-l-red-500" : b.risk_bucket === "medium" ? "text-yellow-400 border-l-yellow-500" : "text-green-400 border-l-green-600";
                    const isSelected = selected?.business_id === b.business_id;
                    return (
                      <button
                        key={b.business_id}
                        onClick={() => setSelected(b)}
                        className={`w-full text-left bg-white/[0.03] border border-white/8 border-l-2 ${color} rounded p-3 hover:bg-white/[0.06] transition-colors ${isSelected ? "ring-1 ring-white/20" : ""}`}
                      >
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-semibold text-white truncate max-w-[160px]">{b.dba_name}</span>
                          <span className={`font-mono text-sm font-bold ${b.risk_bucket === "high" ? "text-red-400" : b.risk_bucket === "medium" ? "text-yellow-400" : "text-green-400"}`}>
                            {(b.risk_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="w-full bg-white/5 rounded-full h-0.5 mt-1.5">
                          <div className="h-0.5 rounded-full" style={{ width: `${b.risk_score * 100}%`, background: b.risk_bucket === "high" ? "#e8293a" : b.risk_bucket === "medium" ? "#f5a623" : "#1a8a50" }} />
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Detail panel */}
            <div className="lg:col-span-3">
              {selected ? (
                <div className="bg-white/[0.02] border border-white/8 rounded-md p-6">
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <h2 className="text-xl font-bold text-white mb-1">{selected.dba_name}</h2>
                      <p className="font-mono text-xs text-white/30">{selected.address}{selected.zip_code ? ` · ${selected.zip_code}` : ""}</p>
                    </div>
                    <ScoreGauge score={selected.risk_score} />
                  </div>

                  <div className="font-mono text-[0.58rem] uppercase tracking-widest text-white/20 border-b border-white/5 pb-2 mb-4">
                    Risk Indicators
                  </div>

                  <div className="space-y-0">
                    {indicators.map((row) => (
                      <div key={row.label} className="flex justify-between items-center py-2.5 border-b border-white/5">
                        <span className="font-mono text-xs text-white/35">{row.label}</span>
                        <span className="font-mono text-xs text-white font-medium">{row.value}</span>
                      </div>
                    ))}
                  </div>

                  <div className={`mt-5 p-3 rounded text-xs font-mono ${
                    selected.risk_bucket === "high"
                      ? "bg-red-500/8 border border-red-500/15 text-red-400"
                      : selected.risk_bucket === "medium"
                      ? "bg-yellow-500/8 border border-yellow-500/15 text-yellow-400"
                      : "bg-green-500/8 border border-green-500/15 text-green-400"
                  }`}>
                    {selected.risk_bucket === "high" && "⚠ This business is in the top risk tier. Businesses at this level close at a 46% rate within 6 months."}
                    {selected.risk_bucket === "medium" && "→ Elevated risk. Businesses in this bucket close at 9.5%, which is 10× the baseline rate."}
                    {selected.risk_bucket === "low" && "✓ Low risk. Less than 1% of businesses in this bucket close within 6 months."}
                  </div>
                </div>
              ) : (
                <div className="border border-white/5 border-dashed rounded-md p-12 flex items-center justify-center">
                  <p className="font-mono text-xs text-white/15 text-center">Select a business from the list<br />to see its full risk profile</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Chicago Map — always visible once search is done, or as default city view */}
        <div className="mt-8">
          <div className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-white/20 border-b border-white/5 pb-2 mb-4 flex items-center gap-3">
            <span>✶ Chicago Map · {results.filter(b => b.latitude).length > 0 ? `${results.filter(b => b.latitude).length} locations pinned` : "City view"}</span>
          </div>
          <ChicagoMap
            height="420px"
            focusMarker={
              selected?.latitude && selected?.longitude
                ? { lat: selected.latitude, lng: selected.longitude }
                : null
            }
            markers={results
              .filter((b) => b.latitude && b.longitude)
              .map((b) => ({
                lat: b.latitude!,
                lng: b.longitude!,
                name: b.dba_name,
                score: b.risk_score,
                bucket: b.risk_bucket,
                address: b.address,
              }))}
          />
        </div>
      </div>
      <Footer />
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#060b11]" />}>
      <SearchPageInner />
    </Suspense>
  );
}
