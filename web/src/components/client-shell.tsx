"use client";

import dynamic from "next/dynamic";

const SmoothCursor = dynamic(
  () => import("@/components/ui/smooth-cursor").then((m) => m.SmoothCursor),
  { ssr: false }
);

export function ClientShell({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <SmoothCursor />
    </>
  );
}
