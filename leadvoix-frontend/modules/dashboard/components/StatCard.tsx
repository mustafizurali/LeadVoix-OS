"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ComponentType<{ className?: string }>;
  accentColor?: "violet" | "cyan" | "emerald" | "amber";
  indicatorText?: string;
}

const colorStyles = {
  violet: {
    iconBg: "bg-[#7657F6]/15 text-[#7657F6] border-[#7657F6]/30",
    glow: "group-hover:border-[#7657F6]/40",
  },
  cyan: {
    iconBg: "bg-[#24C8D8]/15 text-[#24C8D8] border-[#24C8D8]/30",
    glow: "group-hover:border-[#24C8D8]/40",
  },
  emerald: {
    iconBg: "bg-[#35D6C1]/15 text-[#35D6C1] border-[#35D6C1]/30",
    glow: "group-hover:border-[#35D6C1]/40",
  },
  amber: {
    iconBg: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    glow: "group-hover:border-amber-500/40",
  },
};

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accentColor = "violet",
  indicatorText,
}: StatCardProps) {
  const styles = colorStyles[accentColor];

  return (
    <div
      className={cn(
        "group relative flex flex-col justify-between rounded-2xl border border-slate-800/80 bg-[#151D32] p-5 shadow-lg shadow-black/40 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-black/60",
        styles.glow
      )}
    >
      <div>
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#AAB4CC]">
            {title}
          </p>
          {Icon && (
            <div
              className={cn(
                "flex h-9 w-9 items-center justify-center rounded-xl border transition-transform duration-200 group-hover:scale-105",
                styles.iconBg
              )}
            >
              <Icon className="h-4 w-4" />
            </div>
          )}
        </div>

        <div className="mt-3 flex items-baseline gap-2">
          <h2 className="text-3xl font-extrabold tracking-tight text-[#F5F7FC]">
            {value}
          </h2>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-slate-800/60 pt-3">
        {subtitle && (
          <p className="text-xs font-medium text-[#AAB4CC]/80">
            {subtitle}
          </p>
        )}
        {indicatorText && (
          <span className="rounded-md bg-slate-800/80 px-2 py-0.5 text-[11px] font-medium text-[#AAB4CC]">
            {indicatorText}
          </span>
        )}
      </div>
    </div>
  );
}
