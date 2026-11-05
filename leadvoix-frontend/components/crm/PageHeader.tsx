"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface PageHeaderBadge {
  label: string;
  variant?: "emerald" | "violet" | "cyan" | "amber";
  pulse?: boolean;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  badge?: string | PageHeaderBadge;
  action?: React.ReactNode;
  actions?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}

const badgeVariants = {
  emerald: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  violet: "bg-[#7657F6]/15 text-[#7657F6] border-[#7657F6]/30",
  cyan: "bg-[#24C8D8]/15 text-[#24C8D8] border-[#24C8D8]/30",
  amber: "bg-amber-500/15 text-amber-400 border-amber-500/30",
};

export function PageHeader({
  title,
  subtitle,
  badge,
  action,
  actions,
  children,
  className,
}: PageHeaderProps) {
  const normalizedBadge: PageHeaderBadge | null =
    typeof badge === "string"
      ? { label: badge, variant: "violet" }
      : badge ?? null;

  const renderedActions = action || actions;

  return (
    <div
      className={cn(
        "flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[#273449]",
        className
      )}
    >
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F5F7FC]">
            {title}
          </h1>

          {normalizedBadge && (
            <span
              className={cn(
                "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider border",
                badgeVariants[normalizedBadge.variant || "violet"]
              )}
            >
              {normalizedBadge.pulse && (
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-current" />
                </span>
              )}
              {normalizedBadge.label}
            </span>
          )}
        </div>

        {subtitle && (
          <p className="mt-1 text-xs sm:text-sm text-[#94A3B8] font-normal leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>

      {(renderedActions || children) && (
        <div className="flex items-center gap-3 shrink-0">
          {renderedActions}
          {children}
        </div>
      )}
    </div>
  );
}
