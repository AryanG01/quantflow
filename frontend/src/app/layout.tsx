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
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen">
        <div className="max-w-[1600px] mx-auto px-4 py-4 md:px-6 md:py-5">
          <SharedHeader />
          {children}
        </div>
      </body>
    </html>
  );
}
