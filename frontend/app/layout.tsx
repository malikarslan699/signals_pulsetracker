import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "PulseSignal Pro — Professional Trading Signals",
  description:
    "Real-time crypto and forex trading signals powered by ICT Smart Money concepts and 35+ professional indicators.",
  keywords: "trading signals, ICT, smart money, crypto signals, forex signals, Binance",
  openGraph: {
    title: "PulseSignal Pro",
    description: "Professional Trading Signals with ICT Smart Money",
    url: "https://signals.pulsetracker.net",
    siteName: "PulseSignal Pro",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-text-primary min-h-screen">
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: "#1F2937",
                color: "#F9FAFB",
                border: "1px solid #374151",
                borderRadius: "8px",
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
