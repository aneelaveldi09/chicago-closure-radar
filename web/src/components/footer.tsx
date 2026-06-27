export function Footer() {
  const year = new Date().getFullYear();
  const chicagoStars = [
    { label: "Fort Dearborn" },
    { label: "Great Fire" },
    { label: "World's Fair" },
    { label: "Century" },
  ];

  return (
    <footer className="mt-16">
      {/* Chicago flag — top blue stripe */}
      <div className="h-px bg-[#1F6CB0]/25 mx-8" />

      {/* Four Chicago flag stars */}
      <div className="py-5 flex flex-col items-center gap-3">
        <div className="flex items-center gap-10">
          {chicagoStars.map((s) => (
            <div key={s.label} className="flex flex-col items-center gap-1.5">
              <span
                className="text-[#e8293a] text-xl leading-none"
                style={{ textShadow: "0 0 10px rgba(232,41,58,0.45)" }}
              >
                ✶
              </span>
              <span className="font-mono text-[0.42rem] uppercase tracking-widest text-white/12">
                {s.label}
              </span>
            </div>
          ))}
        </div>
        <p className="font-mono text-[0.5rem] uppercase tracking-[0.25em] text-[#1F6CB0]/30">
          Chicago Flag · Est. 1917
        </p>
      </div>

      {/* Chicago flag — bottom blue stripe */}
      <div className="h-px bg-[#1F6CB0]/25 mx-8" />

      {/* Footer content */}
      <div className="border-t border-white/5 px-8 py-5 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          <span className="font-mono text-[0.62rem] text-white/20 uppercase tracking-widest">
            Chicago Closure Radar
          </span>
          <span className="font-mono text-[0.5rem] text-[#1F6CB0]/30 uppercase tracking-widest hidden sm:inline">
            · The City That Works
          </span>
        </div>
        <p className="font-mono text-[0.62rem] text-white/20">
          © {year} Aneela Veldi · Built on City of Chicago open data
        </p>
        <div className="flex items-center gap-4 font-mono text-[0.62rem] text-white/20">
          <a
            href="https://github.com/aneelaveldi09/chicago-closure-radar"
            target="_blank"
            rel="noopener"
            className="hover:text-white/50 transition-colors"
          >
            GitHub
          </a>
          <a
            href="https://data.cityofchicago.org"
            target="_blank"
            rel="noopener"
            className="hover:text-white/50 transition-colors"
          >
            Data Source
          </a>
        </div>
      </div>
    </footer>
  );
}
