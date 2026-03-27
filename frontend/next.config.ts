import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    domains: ["signals.pulsetracker.net", "api.pulsetracker.net"],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL || "http://backend:8000"}/api/:path*`,
      },
    ];
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "https://api.pulsetracker.net",
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || "wss://api.pulsetracker.net",
    NEXT_PUBLIC_APP_NAME: "PulseSignal Pro",
    NEXT_PUBLIC_APP_DOMAIN: "signals.pulsetracker.net",
  },
};

export default nextConfig;
