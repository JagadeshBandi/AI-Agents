import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TapApply — Autonomous Job Application Platform",
  description:
    "Your autonomous job search partner. Apply smarter, not harder. TapApply scans, applies, and tracks jobs across UK, USA, Canada and more — all on autopilot.",
  keywords: ["job applications", "autopilot", "job search", "AI", "resume", "career"],
  authors: [{ name: "TapApply" }],
  robots: "noindex, nofollow",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#09090b",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#050812] text-zinc-50 antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
