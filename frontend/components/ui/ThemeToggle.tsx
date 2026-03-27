"use client";
import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

export function ThemeToggle() {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    // Read saved preference; default to dark
    const saved = localStorage.getItem("theme");
    const dark = saved !== "light";
    setIsDark(dark);
    if (dark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const toggle = () => {
    const next = !isDark;
    setIsDark(next);
    if (next) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  return (
    <button
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="relative p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-2 border border-transparent hover:border-border transition-all duration-200"
    >
      <span
        className="absolute inset-0 flex items-center justify-center transition-all duration-300"
        style={{ opacity: isDark ? 1 : 0, transform: isDark ? "scale(1)" : "scale(0.7) rotate(90deg)" }}
      >
        <Moon className="w-4 h-4" />
      </span>
      <span
        className="flex items-center justify-center transition-all duration-300"
        style={{ opacity: isDark ? 0 : 1, transform: isDark ? "scale(0.7) rotate(-90deg)" : "scale(1)" }}
      >
        <Sun className="w-4 h-4 text-gold" />
      </span>
    </button>
  );
}
