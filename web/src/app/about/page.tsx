"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { Footer } from "@/components/footer";

const FlickeringGrid = dynamic(
  () => import("@/components/ui/flickering-grid").then((m) => m.FlickeringGrid),
  { ssr: false }
);

const STACK = [
  { layer: "Data",     items: ["City of Chicago Data Portal", "Business Licenses API", "Food Inspections API", "Socrata / SODA query engine"] },
  { layer: "ML",       items: ["Python 3.11", "XGBoost 2.x", "SHAP (TreeExplainer)", "scikit-learn", "pandas + numpy"] },
  { layer: "Backend",  items: ["FastAPI", "Uvicorn", "Render (free tier)", "Parquet (pyarrow)"] },
  { layer: "Frontend", items: ["Next.js 14 App Router", "TypeScript", "Tailwind CSS", "shadcn/ui", "motion/react", "three.js / GLSL shaders"] },
];

const STEPS = [
  {
    num: "01",
    title: "Collect the data",
    body: "We pull two live datasets from the City of Chicago Data Portal: Business Licenses (193K+ records) and Food Inspections (312K+ records). Both are refreshed regularly via the Socrata API. No scraping, no static dumps.",
  },
  {
    num: "02",
    title: "Build ground truth",
    body: "A business is labeled \"closed\" if its license status is AAC (cancelled) or REV (revoked), or if a city inspector recorded \"Out of Business\" as the result. We merge both sources to form a deduplicated ground-truth set of ~530 confirmed closures.",
  },
  {
    num: "03",
    title: "Engineer features from inspections",
    body: "For each business we compute: days since the last inspection, violation rate over 180/365/730-day windows, an all-time fail rate, a linear trend through inspection results (slope), and consecutive fail streaks. These become the model's input signals.",
  },
  {
    num: "04",
    title: "Train with XGBoost",
    body: "We train an XGBoost classifier on snapshots: features computed as of date X, label = closed within 6 months after X. Class imbalance (97/3) is handled via scale_pos_weight. 5-fold cross-validation yields ROC-AUC 0.807.",
  },
  {
    num: "05",
    title: "Explain with SHAP",
    body: "TreeExplainer decomposes each prediction into feature contributions. The single biggest signal: days since last inspection. A business that goes dark with no city inspection for a long time is the strongest predictor of closure, ranking above violation counts, fail rates, and trends.",
  },
  {
    num: "06",
    title: "Validate the lift",
    body: "We bucket predictions into HIGH / MEDIUM / LOW and measure actual closure rates. The HIGH bucket closes at 46.4% (46× the 1% baseline). MEDIUM closes at 9.5%, still 10× baseline. This lift is the proof: the model is learning real signal, not noise.",
  },
];

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#060b11] text-[#c4d4e8]">

      {/* Nav */}
      <nav className="sticky top-0 z-50 flex items-center justify-between px-8 h-13 border-b border-white/5 bg-[#060b11]/90 backdrop-blur-md">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
          <span className="font-mono text-sm font-bold text-white tracking-widest">CLOSURE RADAR</span>
          <span className="hidden sm:flex items-center gap-1 ml-1">
            {["✶","✶","✶","✶"].map((s, i) => (
              <span key={i} className="text-[#e8293a] text-[0.6rem]" style={{ textShadow: "0 0 5px rgba(232,41,58,0.5)" }}>{s}</span>
            ))}
          </span>
        </Link>
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="font-mono text-xs uppercase tracking-widest text-white/30 hover:text-red-400 transition-colors">Dashboard</Link>
          <Link href="/search" className="font-mono text-xs uppercase tracking-widest text-white/30 hover:text-red-400 transition-colors">Search</Link>
          <span className="font-mono text-xs text-white/20 uppercase tracking-widest">About</span>
        </div>
      </nav>

      {/* Breadcrumb */}
      <div className="px-8 py-3 border-b border-white/5 flex items-center gap-2 font-mono text-[0.6rem] text-white/20 uppercase tracking-widest">
        <Link href="/" className="hover:text-white/50 transition-colors">Home</Link>
        <span className="text-white/10">/</span>
        <span className="text-white/40">How We Built It</span>
      </div>

      {/* Hero with FlickeringGrid */}
      <div className="relative overflow-hidden border-b border-white/5">
        <div className="absolute inset-0 z-0">
          <FlickeringGrid
            color="rgb(232,41,58)"
            maxOpacity={0.04}
            flickerChance={0.08}
            squareSize={3}
            gridGap={8}
            className="w-full h-full"
          />
        </div>
        <div className="relative z-10 max-w-4xl mx-auto px-8 py-20">
          <div className="flex items-center gap-3 mb-4">
            <span className="font-mono text-[0.6rem] uppercase tracking-[0.25em] text-red-500">How We Built It</span>
            <span className="font-mono text-[0.5rem] text-[#1F6CB0]/40 uppercase tracking-widest">312 · Chicago, IL</span>
          </div>
          <h1 className="font-mono text-4xl lg:text-5xl font-bold text-white leading-tight mb-6">
            Six months before<br />
            <span className="text-red-500">the lights go out</span>
          </h1>
          <p className="text-white/50 text-lg leading-relaxed max-w-2xl mb-8">
            A machine learning system that reads city inspection records like a doctor reads vital signs,
            catching the slow deterioration that precedes a café closure months before it happens.
            Built entirely on open government data.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { v: "0.807", l: "ROC-AUC" },
              { v: "46×",   l: "Lift in high-risk bucket" },
              { v: "530",   l: "Confirmed closures" },
              { v: "19K+",  l: "Businesses tracked" },
            ].map((k) => (
              <div key={k.l} className="border border-white/8 rounded-md p-4 bg-white/[0.02]">
                <p className="font-mono text-2xl font-bold text-white mb-0.5">{k.v}</p>
                <p className="font-mono text-[0.6rem] uppercase tracking-widest text-white/25">{k.l}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How it works — steps */}
      <div className="max-w-4xl mx-auto px-8 py-16">
        <div className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-white/20 border-b border-white/5 pb-2 mb-10">
          ✶ Methodology: Step by Step
        </div>
        <div className="space-y-0">
          {STEPS.map((s, i) => (
            <div key={s.num} className={`flex gap-8 py-8 ${i < STEPS.length - 1 ? "border-b border-white/5" : ""}`}>
              <div className="shrink-0 pt-0.5">
                <span className="font-mono text-3xl font-bold text-white/8">{s.num}</span>
              </div>
              <div>
                <h2 className="font-mono text-lg font-bold text-white mb-3">{s.title}</h2>
                <p className="text-white/45 leading-relaxed text-sm">{s.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Model results */}
      <div className="border-t border-white/5 bg-white/[0.01]">
        <div className="max-w-4xl mx-auto px-8 py-16">
          <div className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-white/20 border-b border-white/5 pb-2 mb-10">
            ✶ Results
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
            {[
              { label: "HIGH",   rate: "46.4%", baseline: "vs 1% baseline", color: "#e8293a", bg: "bg-red-500/5 border-red-500/15" },
              { label: "MEDIUM", rate:  "9.5%", baseline: "vs 1% baseline", color: "#f5a623", bg: "bg-yellow-500/5 border-yellow-500/15" },
              { label: "LOW",    rate:  "0.9%", baseline: "matches baseline", color: "#1a8a50", bg: "bg-green-500/5 border-green-500/15" },
            ].map((r) => (
              <div key={r.label} className={`border rounded-md p-5 ${r.bg}`}>
                <p className="font-mono text-[0.6rem] uppercase tracking-widest mb-2" style={{ color: r.color }}>{r.label} risk</p>
                <p className="font-mono text-3xl font-bold text-white mb-1">{r.rate}</p>
                <p className="font-mono text-[0.62rem] text-white/30">closure rate · {r.baseline}</p>
              </div>
            ))}
          </div>
          <p className="text-white/35 text-sm leading-relaxed max-w-2xl">
            The model achieves 0.807 ROC-AUC with 5-fold cross-validation. The HIGH-risk bucket
            concentrates real closures at 46× the background rate. If you only acted on
            the flagged set, you would catch 46× more closures per inspection than random sampling.
          </p>
        </div>
      </div>

      {/* Tech stack */}
      <div className="border-t border-white/5">
        <div className="max-w-4xl mx-auto px-8 py-16">
          <div className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-white/20 border-b border-white/5 pb-2 mb-10">
            ✶ Tech Stack
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {STACK.map((s) => (
              <div key={s.layer} className="bg-white/[0.02] border border-white/8 rounded-md p-4">
                <p className="font-mono text-[0.6rem] uppercase tracking-widest text-red-500 mb-3">{s.layer}</p>
                <ul className="space-y-1.5">
                  {s.items.map((item) => (
                    <li key={item} className="font-mono text-[0.65rem] text-white/40 flex items-center gap-1.5">
                      <span className="w-1 h-1 rounded-full bg-white/20 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Data sources */}
      <div className="border-t border-white/5 bg-white/[0.01]">
        <div className="max-w-4xl mx-auto px-8 py-16">
          <div className="font-mono text-[0.6rem] uppercase tracking-[0.2em] text-white/20 border-b border-white/5 pb-2 mb-8">
            ✶ Data Sources: 100% Open
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                name: "Business Licenses",
                portal: "data.cityofchicago.org",
                endpoint: "r5kz-chrr.json",
                records: "193K+ records",
                desc: "All food-service license records for Chicago. Used for business metadata, license status, and closure ground truth.",
              },
              {
                name: "Food Inspections",
                portal: "data.cityofchicago.org",
                endpoint: "4ijn-s7e5.json",
                records: "312K+ records",
                desc: "Every city health inspection since 2010. Used to compute fail rates, violation trends, inspection frequency, and consecutive fail streaks.",
              },
            ].map((d) => (
              <div key={d.name} className="bg-white/[0.02] border border-white/8 rounded-md p-5">
                <p className="font-mono text-sm font-bold text-white mb-1">{d.name}</p>
                <p className="font-mono text-[0.6rem] text-[#1F6CB0]/50 mb-3">{d.portal} · {d.endpoint}</p>
                <p className="font-mono text-[0.62rem] text-red-400 mb-3">{d.records}</p>
                <p className="text-white/35 text-xs leading-relaxed">{d.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="border-t border-white/5">
        <div className="max-w-4xl mx-auto px-8 py-12 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div>
            <p className="font-mono text-sm font-bold text-white mb-1">See it live</p>
            <p className="font-mono text-[0.62rem] text-white/30">Check the live radar and search any Chicago business</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard"
              className="font-mono text-xs uppercase tracking-widest px-5 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded transition-colors"
            >
              Open Radar
            </Link>
            <a
              href="https://github.com/aneelaveldi09/chicago-closure-radar"
              target="_blank"
              rel="noopener"
              className="font-mono text-xs uppercase tracking-widest px-5 py-2.5 border border-white/10 hover:border-white/30 text-white/50 hover:text-white rounded transition-colors"
            >
              GitHub
            </a>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
