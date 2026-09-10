import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "NFT Manufacturing Intelligence",
  description: "Next-Gen Factory Technologies — Phase 0 foundation.",
  robots: { index: false, follow: false },
};
export const dynamic = "force-dynamic";
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en-CA">
      <body>{children}</body>
    </html>
  );
}
