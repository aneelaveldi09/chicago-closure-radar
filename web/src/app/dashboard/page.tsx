"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, TrendingDown, Building2, Activity, ArrowUpRight } from "lucide-react";
import { Footer } from "@/components/footer";
import { AnimatedList } from "@/components/ui/animated-list";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Business {
  business_id: string;
  dba_name: string;
  risk_score: number;
  risk_bucket: string;
  days_since_last_inspection?: number;
  all_time_fail_rate?: number;
  all_time_violations_per_insp?: number;
  address?: string;
  zip_code?: string;
}

interface Stats {
  total_businesses: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  high_risk_pct: number;
  confirmed_closed: number;
  model_roc_auc: number;
}

function RiskBar({ score }: { score: number }) {
  const color = score >= 0.66 ? "#e8293a" : score >= 0.33 ? "#f5a623" : "#1a8a50";
  return (
    <div className="w-full bg-white/5 rounded-full h-1 mt-1">
      <div className="h-1 rounded-full transition-all duration-500" style={{ width: `${score * 100}%`, background: color }} />
    </div>
  );
}

function RiskBadge({ bucket }: { bucket: string }) {
  const styles: Record<string, string> = {
    high:   "bg-red-500/10 text-red-400 border border-red-500/20",
    medium: "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20",
    low:    "bg-green-500/10 text-green-400 border border-green-500/20",
  };
  return (
    <span className={`font-mono text-[0.6rem] uppercase tracking-widest px-2 py-0.5 rounded ${styles[bucket] ?? ""}`}>
      {bucket}
    </span>
  );
}

function BusinessCard({ b }: { b: Business }) {
  const borderColor = b.risk_bucket === "high" ? "border-l-red-500" : b.risk_bucket === "medium" ? "border-l-yellow-500" : "border-l-green-600";
  return (
    <div className={`bg-white/[0.03] border border-white/8 border-l-2 ${borderColor} rounded-md p-3 hover:bg-white/[0.05] transition-colors`}>
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <p className="font-semibold text-white text-sm leading-tight truncate max-w-[200px]">
          {b.dba_name ?? "—"}
        </p>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`font-mono text-sm font-bold ${b.risk_bucket === "high" ? "text-red-400" : b.risk_bucket === "medium" ? "text-yellow-400" : "text-green-400"}`}>
            {(b.risk_score * 100).toFixed(0)}%
          </span>
          <RiskBadge bucket={b.risk_bucket} />
        </div>
      </div>
      <RiskBar score={b.risk_score} />
      <div className="flex gap-3 mt-1.5 font-mono text-[0.62rem] text-white/30">
        {b.days_since_last_inspection != null && (
          <span>{b.days_since_last_inspection}d dark</span>
        )}
        {b.all_time_fail_rate != null && (
          <span>{(b.all_time_fail_rate * 100).toFixed(0)}% fail rate</span>
        )}
        {b.all_time_violations_per_insp != null && (
          <span>{b.all_time_violations_per_insp.toFixed(1)} viol/insp</span>
        )}
        {b.address && <span className="truncate max-w-[140px]">{b.address}</span>}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [topRisk, setTopRisk] = useState<Business[]>([]);
  const [loading, setLoading] = useState(true);
  const [time, setTime] = useState("");
  const [activeTab, setActiveTab] = useState<"high" | "medium">("high");

  useEffect(() => {
    const tick = () => setTime(new Date().toLocaleTimeString("en-US", { hour12: false }));
    tick(); const id = setInterval(tick, 1000); return () => clearInterval(id);
  }, []);

  useEffect(() => {
    async function load() {
      try {
        const [s, t] = await Promise.all([
          fetch(`${API}/stats`).then((r) => r.json()),
          fetch(`${API}/top-risk?n=50`).then((r) => r.json()),
        ]);
        setStats(s); setTopRisk(t);
      } catch { /* API not running — show skeleton */ }
      finally { setLoading(false); }
    }
    load();
  }, []);

  const filtered = topRisk.filter((b) => b.risk_bucket === activeTab);

  return (
    <div className="min-h-screen bg-[#060b11] text-[#c4d4e8]">

      {/* Nav */}
      <nav className="sticky top-0 z-50 flex items-center justify-between px-8 h-13 border-b border-white/5 bg-[#060b11]/90 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse" />
            <span className="font-mono text-sm font-bold text-white tracking-widest">CLOSURE RADAR</span>
            <span className="hidden sm:flex items-center gap-1 ml-1">
              {["✶","✶","✶","✶"].map((s, i) => (
                <span key={i} className="text-[#e8293a] text-[0.6rem] leading-none" style={{ textShadow: "0 0 5px rgba(232,41,58,0.5)" }}>{s}</span>
              ))}
            </span>
          </Link>
          <span className="text-white/10 px-2">|</span>
          <span className="font-mono text-xs text-white/30 uppercase tracking-widest">Dashboard</span>
        </div>
        <div className="flex items-center gap-6">
          <Link href="/search" className="font-mono text-xs uppercase tracking-widest text-white/30 hover:text-red-400 transition-colors">Search</Link>
          <span className="font-mono text-xs text-white/20">{time}</span>
        </div>
      </nav>

      {/* Ticker */}
      {topRisk.length > 0 && (
        <div className="bg-red-950/30 border-b border-red-500/10 overflow-hidden h-8 flex items-center">
          <div className="shrink-0 font-mono text-[0.6rem] text-red-500 uppercase tracking-widest px-4 border-r border-red-500/20 h-full flex items-center">
            <span className="text-[#e8293a]">✶</span> LIVE FEED
          </div>
          <div className="overflow-hidden flex-1">
            <div className="inline-flex items-center gap-8 font-mono text-[0.65rem] animate-[marquee_40s_linear_infinite] whitespace-nowrap px-8">
              {topRisk.filter(b => b.risk_bucket === "high").slice(0, 12).map((b) => (
                <span key={b.business_id} className="flex items-center gap-2">
                  <span className="text-red-400 font-bold">✶ {b.dba_name}</span>
                  <span className="text-white/30">{(b.risk_score * 100).toFixed(0)}%</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-8 py-8">

        {/* Section label */}
        <div className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-white/20 border-b border-white/5 pb-2 mb-6 flex items-center gap-3">
          <span>✶ City Overview · Chicago, IL 60601 · Live Feed ✶</span>
          <span className="text-[#1F6CB0]/30 font-mono text-[0.5rem]">The City That Works</span>
        </div>

        {/* KPI Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
          {[
            { icon: Building2, label: "Tracked", value: stats?.total_businesses.toLocaleString() ?? "—", sub: "food businesses" },
            { icon: AlertTriangle, label: "High Risk", value: stats?.high_risk.toLocaleString() ?? "—", sub: `${((stats?.high_risk_pct ?? 0)*100).toFixed(1)}% of total`, danger: true },
            { icon: TrendingDown, label: "Confirmed Closed", value: stats?.confirmed_closed.toLocaleString() ?? "—", sub: "ground truth labels" },
            { icon: Activity, label: "Model AUC", value: stats?.model_roc_auc.toFixed(3) ?? "—", sub: "XGBoost · 5-fold CV" },
          ].map((k) => (
            <div key={k.label} className="bg-white/[0.03] border border-white/8 rounded-md p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-[0.58rem] uppercase tracking-widest text-white/25">{k.label}</span>
                <k.icon size={13} className="text-white/15" />
              </div>
              <div className={`font-mono text-2xl font-bold mb-1 ${k.danger ? "text-red-400" : "text-white"}`}>
                {loading ? <span className="text-white/10">—</span> : k.value}
              </div>
              <div className="font-mono text-[0.6rem] text-white/20">{k.sub}</div>
            </div>
          ))}
        </div>

        {/* Main split */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Risk feed */}
          <div className="lg:col-span-2">
            <div className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-white/20 border-b border-white/5 pb-2 mb-4">
              Risk Feed
            </div>

            {/* Tabs */}
            <div className="flex gap-0 border-b border-white/5 mb-4">
              {(["high", "medium"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`font-mono text-[0.62rem] uppercase tracking-widest px-4 py-2 border-b-2 transition-colors ${
                    activeTab === tab
                      ? tab === "high" ? "text-red-400 border-red-400" : "text-yellow-400 border-yellow-400"
                      : "text-white/20 border-transparent hover:text-white/40"
                  }`}
                >
                  {tab} ({topRisk.filter(b => b.risk_bucket === tab).length})
                </button>
              ))}
            </div>

            {loading ? (
              <div className="space-y-2">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="h-16 rounded-md bg-white/[0.03] animate-pulse" />
                ))}
              </div>
            ) : filtered.length === 0 ? (
              <p className="font-mono text-xs text-white/20 py-8">No businesses in this risk bucket.</p>
            ) : (
              <div className="max-h-[620px] overflow-y-auto pr-1">
                <AnimatedList delay={120} className="gap-2 items-stretch">
                  {filtered.map((b) => (
                    <div key={b.business_id} className="w-full">
                      <BusinessCard b={b} />
                    </div>
                  ))}
                </AnimatedList>
              </div>
            )}
          </div>

          {/* Right panel */}
          <div className="space-y-6">

            {/* Closure lift */}
            <div>
              <div className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-white/20 border-b border-white/5 pb-2 mb-4">
                Closure Rate by Risk Bucket
              </div>
              {[
                { label: "High",   rate: 46.4, color: "#e8293a", count: stats?.high_risk },
                { label: "Medium", rate: 9.5,  color: "#f5a623", count: stats?.medium_risk },
                { label: "Low",    rate: 0.9,  color: "#1a8a50", count: stats?.low_risk },
              ].map((row) => (
                <div key={row.label} className="mb-3">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-mono text-xs" style={{ color: row.color }}>{row.label}</span>
                    <span className="font-mono text-xs font-bold text-white">{row.rate}%</span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-1.5">
                    <div className="h-1.5 rounded-full" style={{ width: `${row.rate * 2}%`, background: row.color }} />
                  </div>
                  <div className="font-mono text-[0.58rem] text-white/20 mt-0.5">{row.count?.toLocaleString()} businesses</div>
                </div>
              ))}
              <div className="mt-3 p-3 bg-red-500/5 border border-red-500/10 rounded-md">
                <p className="font-mono text-[0.62rem] text-red-400">
                  HIGH-risk businesses close at 46× the baseline rate.
                </p>
              </div>
            </div>

            {/* Top signals */}
            <div>
              <div className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-white/20 border-b border-white/5 pb-2 mb-4">
                Top Predictors (SHAP)
              </div>
              {[
                { name: "days_since_last_inspection", pct: 100 },
                { name: "all_time_violations / insp",  pct: 18 },
                { name: "violations_180d",             pct: 14 },
                { name: "result_trend",                pct: 13 },
                { name: "total_inspections",           pct: 12 },
                { name: "all_time_fail_rate",          pct: 9 },
              ].map((f) => (
                <div key={f.name} className="mb-2">
                  <div className="flex justify-between mb-0.5">
                    <span className="font-mono text-[0.62rem] text-white/40 truncate max-w-[180px]">{f.name}</span>
                    <span className="font-mono text-[0.62rem] text-white/25">{f.pct}</span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-0.5">
                    <div className="h-0.5 rounded-full bg-white/30" style={{ width: `${f.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Neighborhood Watch */}
            <div>
              <div className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-white/20 border-b border-white/5 pb-2 mb-4">
                ✶ Neighborhood Watch
              </div>
              {[
                { hood: "Wicker Park",    count: 12, pct: 100 },
                { hood: "Logan Square",   count:  8, pct: 67 },
                { hood: "Pilsen",         count:  6, pct: 50 },
                { hood: "Hyde Park",      count:  5, pct: 42 },
                { hood: "Lincoln Square", count:  3, pct: 25 },
              ].map((n) => (
                <div key={n.hood} className="mb-2.5">
                  <div className="flex justify-between mb-0.5">
                    <span className="font-mono text-[0.62rem] text-white/35">{n.hood}</span>
                    <span className="font-mono text-[0.62rem] text-[#e8293a] font-bold">{n.count} alerts</span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-0.5">
                    <div className="h-0.5 rounded-full bg-[#e8293a]/40" style={{ width: `${n.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>

            {/* CTA */}
            <Link href="/search" className="flex items-center justify-between p-4 bg-red-500/5 border border-red-500/15 rounded-md hover:bg-red-500/10 transition-colors group">
              <div>
                <p className="font-mono text-xs text-red-400 font-bold mb-0.5">Search a business</p>
                <p className="font-mono text-[0.62rem] text-white/30">Look up any Chicago café, restaurant, or bookstore</p>
              </div>
              <ArrowUpRight size={16} className="text-red-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </Link>
          </div>
        </div>
      </div>

      <Footer />

      <style jsx global>{`
        @keyframes marquee {
          from { transform: translateX(0); }
          to   { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
