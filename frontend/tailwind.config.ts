import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background:       "rgb(var(--color-background) / <alpha-value>)",
        surface:          "rgb(var(--color-surface) / <alpha-value>)",
        "surface-2":      "rgb(var(--color-surface-2) / <alpha-value>)",
        border:           "rgb(var(--color-border) / <alpha-value>)",
        "border-light":   "rgb(var(--color-border-light) / <alpha-value>)",
        long:             "rgb(var(--color-long) / <alpha-value>)",
        "long-dim":       "rgb(var(--color-long-dim) / <alpha-value>)",
        short:            "rgb(var(--color-short) / <alpha-value>)",
        "short-dim":      "rgb(var(--color-short-dim) / <alpha-value>)",
        gold:             "rgb(var(--color-gold) / <alpha-value>)",
        purple:           "rgb(var(--color-purple) / <alpha-value>)",
        blue:             "rgb(var(--color-blue) / <alpha-value>)",
        "text-primary":   "rgb(var(--color-text-primary) / <alpha-value>)",
        "text-secondary": "rgb(var(--color-text-secondary) / <alpha-value>)",
        "text-muted":     "rgb(var(--color-text-muted) / <alpha-value>)",
        "text-faint":     "rgb(var(--color-text-faint) / <alpha-value>)",
        success: "rgb(var(--color-long) / <alpha-value>)",
        warning: "rgb(var(--color-gold) / <alpha-value>)",
        danger:  "rgb(var(--color-short) / <alpha-value>)",
        info:    "rgb(var(--color-blue) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        "card-hover":  "0 14px 44px -8px rgb(0 0 0 / 0.32)",
        "glow-long":   "0 0 28px rgb(var(--color-long) / 0.22)",
        "glow-short":  "0 0 28px rgb(var(--color-short) / 0.22)",
        "glow-purple": "0 0 28px rgb(var(--color-purple) / 0.28)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-up":   "slideUp 0.3s ease-out",
        "fade-in":    "fadeIn 0.25s ease-out",
        "fade-up":    "fadeUp 0.3s ease-out",
        blink:        "blink 1s step-end infinite",
      },
      keyframes: {
        slideUp: {
          "0%":   { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)",    opacity: "1" },
        },
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeUp: {
          "0%":   { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        blink: {
          "0%, 100%": { opacity: "1" },
          "50%":      { opacity: "0" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
