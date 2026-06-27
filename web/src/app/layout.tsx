import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import { ClientShell } from "@/components/client-shell";
import "./globals.css";

const sans = IBM_Plex_Sans({ subsets: ["latin"], weight: ["300","400","600","700"], variable: "--font-sans" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["300","400","600","700"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Chicago Closure Radar",
  description: "Real-time closure risk scores for Chicago food businesses. ML-powered early warning system flagging closures months before they happen.",
  keywords: ["Chicago", "restaurant closures", "risk score", "machine learning"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable} dark`}>
      <body className="bg-background text-foreground antialiased min-h-screen">
        <ClientShell>{children}</ClientShell>
      </body>
    </html>
  );
}
