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

// Inline script runs synchronously before paint — prevents theme flash
const themeScript = `(function(){try{var t=localStorage.getItem('theme');if(t==='dark'){document.documentElement.classList.add('dark')}else{document.documentElement.classList.remove('dark');if(!t){localStorage.setItem('theme','light')}}}catch(e){document.documentElement.classList.remove('dark')}})();`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Theme init before first paint — no flash */}
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="bg-background text-text-primary min-h-screen">
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: "rgb(var(--color-surface))",
                color: "rgb(var(--color-text-primary))",
                border: "1px solid rgb(var(--color-border))",
                borderRadius: "10px",
                fontSize: "14px",
                boxShadow: "0 8px 32px rgb(0 0 0 / 0.2)",
              },
              success: {
                iconTheme: { primary: "#10B981", secondary: "white" },
              },
              error: {
                iconTheme: { primary: "#EF4444", secondary: "white" },
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
