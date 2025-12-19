import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";

export const metadata: Metadata = {
  title: "CyberNexus - Unified Threat Intelligence Platform",
  description:
    "Monitor, correlate, and respond to cyber threats in real-time with CyberNexus - your unified threat intelligence command center.",
  keywords: [
    "threat intelligence",
    "cybersecurity",
    "dark web monitoring",
    "credential leak",
    "security operations",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
      </head>
      <body className="min-h-screen bg-[#0a0e1a] text-white antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
