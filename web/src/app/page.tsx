"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Terminal, TypingAnimation, AnimatedSpan } from "@/components/ui/terminal";
import { Backlight } from "@/components/ui/backlight";
import { ShimmerButton } from "@/components/ui/shimmer-button";

const StarshipShader = dynamic(
  () => import("@/components/ui/starship-shader").then((m) => m.StarshipShader),
  { ssr: false }
);

const STATS = {
  businesses: "19,094",
  highRisk: "541",
  confirmed: "530",
  auc: "0.807",
};

const NEIGHBORHOODS = [
  "The Loop", "Wicker Park", "Pilsen", "Logan Square",
  "Hyde Park", "River North", "Lincoln Square", "Bridgeport",
  "Rogers Park", "Gold Coast", "Old Town", "Andersonville",
];

export default function Home() {
  const [time, setTime] = useState("");
  useEffect(() => {
    const tick = () => setTime(new Date().toLocaleTimeString("en-US", { hour12: false }));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <main className="relative min-h-screen overflow-hidden bg-black">

      {/* ── Fullscreen shader background ── */}
      <div className="absolute inset-0 z-0 opacity-60">
        <StarshipShader />
      </div>

      {/* Dark overlay gradients — pointer-events-none so they never block clicks */}
      <div className="absolute inset-0 z-10 bg-gradient-to-b from-black/40 via-transparent to-black/90 pointer-events-none" />
      <div className="absolute inset-0 z-10 bg-gradient-to-r from-black/60 via-transparent to-black/60 pointer-events-none" />

      {/* ── Nav ── */}
      <nav className="absolute top-0 left-0 right-0 z-30 flex items-center justify-between px-8 h-14 border-b border-white/5 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse" />
          <span className="font-mono text-sm font-bold text-white tracking-widest">CHICAGO CLOSURE RADAR</span>
          <span className="hidden sm:flex items-center gap-1.5 ml-1">
            {["✶","✶","✶","✶"].map((s, i) => (
              <span key={i} className="text-[#e8293a] text-[0.65rem] leading-none" style={{ textShadow: "0 0 6px rgba(232,41,58,0.55)" }}>{s}</span>
            ))}
          </span>
        </div>
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="font-mono text-xs uppercase tracking-widest text-white/40 hover:text-red-400 transition-colors">Dashboard</Link>
          <Link href="/search" className="font-mono text-xs uppercase tracking-widest text-white/40 hover:text-red-400 transition-colors">Search</Link>
          <Link href="/about" className="font-mono text-xs uppercase tracking-widest text-white/40 hover:text-red-400 transition-colors">About</Link>
          <span className="font-mono text-xs text-white/20">{time}</span>
        </div>
      </nav>

      {/* Chicago flag top blue stripe */}
      <div className="absolute top-14 left-0 right-0 z-20 h-[1px] bg-[#1F6CB0]/20 pointer-events-none" />

      {/* Hero content — z-40 ensures it's above all decorative layers */}
      <div className="relative z-40 flex min-h-screen items-center">
        <div className="max-w-7xl mx-auto px-8 w-full pt-14">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

            {/* Left: headline */}
            <div>
              <div className="flex items-center gap-3 mb-5">
                <p className="font-mono text-xs font-semibold text-red-500 uppercase tracking-[0.25em]">
                  ML-powered early warning system
                </p>
                <span className="font-mono text-[0.55rem] text-[#1F6CB0]/40 uppercase tracking-widest hidden md:inline">
                  312 · Chicago, IL
                </span>
              </div>

              <h1 className="font-mono text-5xl lg:text-6xl font-bold text-white leading-[1.05] tracking-tight mb-6">
                Which Chicago<br />
                <span className="text-red-500">café closes</span><br />
                next?
              </h1>

              <p className="text-white/50 text-lg leading-relaxed max-w-md mb-4">
                We track 19,000+ food businesses across Chicago using city
                inspection records, violation trends, and failure streaks —
                flagging closures months before they happen.
              </p>

              {/* Chicago neighborhood tags */}
              <div className="flex flex-wrap gap-1.5 mb-8">
                {NEIGHBORHOODS.map((n) => (
                  <span key={n} className="font-mono text-[0.52rem] uppercase tracking-widest px-2 py-0.5 rounded border border-[#1F6CB0]/12 text-[#1F6CB0]/30">
                    {n}
                  </span>
                ))}
              </div>

              {/* KPI row */}
              <div className="grid grid-cols-4 gap-4 mb-10">
                {[
                  { label: "Tracked", value: STATS.businesses },
                  { label: "High Risk", value: STATS.highRisk, danger: true },
                  { label: "Confirmed", value: STATS.confirmed },
                  { label: "Model AUC", value: STATS.auc },
                ].map((k) => (
                  <div key={k.label} className="border border-white/10 rounded-md p-3 bg-white/5 backdrop-blur-sm">
                    <p className="font-mono text-[0.6rem] uppercase tracking-widest text-white/30 mb-1">{k.label}</p>
                    <p className={`font-mono text-xl font-bold ${k.danger ? "text-red-500" : "text-white"}`}>{k.value}</p>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-4">
                <Link href="/dashboard">
                  <ShimmerButton
                    shimmerColor="rgba(255,255,255,0.4)"
                    background="rgba(232,41,58,1)"
                    borderRadius="6px"
                    className="font-mono text-xs uppercase tracking-widest"
                  >
                    Open Radar →
                  </ShimmerButton>
                </Link>
                <a
                  href="https://github.com/aneelaveldi09/chicago-closure-radar"
                  target="_blank"
                  rel="noopener"
                  className="inline-flex items-center gap-2 border border-white/10 hover:border-white/30 text-white/50 hover:text-white font-mono text-xs uppercase tracking-widest px-6 py-3 rounded transition-colors"
                >
                  GitHub
                </a>
              </div>
            </div>

            {/* Right: terminal + backlight */}
            <div className="flex justify-center lg:justify-end">
              <Backlight blur={28} className="relative">
                <Terminal
                  className="bg-black/80 border-white/10 w-[440px] backdrop-blur-md shadow-2xl"
                  sequence
                  startOnView={false}
                >
                  <TypingAnimation className="text-red-400">
                    $ chicago-closure-radar --scan --city chicago
                  </TypingAnimation>
                  <AnimatedSpan className="text-white/40">
                    ✔ Connected to Chicago Data Portal
                  </AnimatedSpan>
                  <AnimatedSpan className="text-white/40">
                    ✔ Loaded 312,312 inspection records
                  </AnimatedSpan>
                  <AnimatedSpan className="text-[#1F6CB0]/60">
                    → Scanning: The Loop · Pilsen · Wicker Park · Logan Sq
                  </AnimatedSpan>
                  <AnimatedSpan className="text-white/40">
                    ✔ Feature engineering complete (77 neighborhoods)
                  </AnimatedSpan>
                  <TypingAnimation className="text-white/60">
                    → Scoring 19,094 businesses...
                  </TypingAnimation>
                  <AnimatedSpan className="text-yellow-400">
                    ⚠ 541 businesses flagged HIGH RISK
                  </AnimatedSpan>
                  <AnimatedSpan className="text-white/40">
                    ──────────────────────────────────────
                  </AnimatedSpan>
                  <AnimatedSpan className="text-red-400 font-bold">
                    ✶ JIMMY JOHNS SANDWICH SHOPS   97.9%
                  </AnimatedSpan>
                  <AnimatedSpan className="text-red-400 font-bold">
                    ✶ TACONTENTO                   97.6%
                  </AnimatedSpan>
                  <AnimatedSpan className="text-red-400 font-bold">
                    ✶ SUGAR BABY&apos;S CAFE       97.0%
                  </AnimatedSpan>
                  <AnimatedSpan className="text-red-400 font-bold">
                    ✶ BABYLON BISTRO               96.2%
                  </AnimatedSpan>
                  <TypingAnimation className="text-green-400">
                    ✔ Alerts sent. Model AUC: 0.807 · 312 proud
                  </TypingAnimation>
                </Terminal>
              </Backlight>
            </div>

          </div>
        </div>
      </div>

      {/* Chicago flag bottom blue stripe */}
      <div className="absolute bottom-12 left-0 right-0 z-20 h-[1px] bg-[#1F6CB0]/15 pointer-events-none" />

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 z-20 bg-gradient-to-t from-black to-transparent pointer-events-none" />

      {/* Copyright + Chicago stars */}
      <div className="absolute bottom-4 left-0 right-0 z-30 flex flex-col items-center gap-1.5 pointer-events-none">
        <div className="flex items-center gap-3">
          {["✶","✶","✶","✶"].map((s, i) => (
            <span key={i} className="text-[#e8293a] text-xs" style={{ textShadow: "0 0 6px rgba(232,41,58,0.5)" }}>{s}</span>
          ))}
        </div>
        <p className="font-mono text-[0.6rem] text-white/20 tracking-widest uppercase">
          © {new Date().getFullYear()} Aneela Veldi · Chicago Closure Radar · The City That Works
        </p>
      </div>
    </main>
  );
}
