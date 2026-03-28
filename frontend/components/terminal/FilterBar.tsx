"use client";
import { useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";

interface FilterOption {
  label: string;
  value: string;
}

interface FilterBarProps {
  segments?: { label: string; options: FilterOption[]; value: string; onChange: (v: string) => void }[];
  onSearch?: (q: string) => void;
  searchPlaceholder?: string;
  showAdvanced?: boolean;
  onAdvancedToggle?: () => void;
  className?: string;
  children?: React.ReactNode;
}

export function FilterBar({
  segments,
  onSearch,
  searchPlaceholder,
  showAdvanced,
  onAdvancedToggle,
  className,
  children,
}: FilterBarProps) {
  const [search, setSearch] = useState("");

  return (
    <div className={cn("flex items-center gap-2 flex-wrap", className)}>
      {onSearch && (
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              onSearch(e.target.value);
            }}
            placeholder={searchPlaceholder || "Search..."}
            className="h-8 pl-7 pr-2 text-xs bg-surface-2 border border-border rounded focus:outline-none focus:ring-1 focus:ring-long w-44"
          />
        </div>
      )}

      {segments?.map((seg) => (
        <div key={seg.label} className="flex items-center gap-0.5">
          {seg.options.map((opt) => (
            <button
              key={opt.value}
              onClick={() => seg.onChange(opt.value)}
              className={cn("filter-pill", seg.value === opt.value && "filter-pill-active")}
            >
              {opt.label}
            </button>
          ))}
        </div>
      ))}

      {children}

      {onAdvancedToggle && (
        <button onClick={onAdvancedToggle} className={cn("filter-pill gap-1", showAdvanced && "filter-pill-active")}>
          <SlidersHorizontal className="h-3 w-3" />
          Filters
        </button>
      )}
    </div>
  );
}
