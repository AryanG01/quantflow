import type { Metadata } from "next";
import "./globals.css";
import { SharedHeader } from "@/components/SharedHeader";

export const metadata: Metadata = {
  title: "QuantFlow | AI Trading System",
  description: "Regime-gated MoE trading dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="scanline min-h-screen">
        <div className="max-w-[1600px] mx-auto p-4 md:p-6">
          <SharedHeader />
          {children}
        </div>
      </body>
    </html>
  );
}
