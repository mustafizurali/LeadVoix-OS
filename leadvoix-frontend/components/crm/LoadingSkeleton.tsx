"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  cols?: number;
  className?: string;
}

export function TableSkeleton({
  rows = 5,
  columns = 5,
  cols,
  className,
}: TableSkeletonProps) {
  const resolvedCols = cols ?? columns;

  return (
    <div
      className={cn(
        "rounded-2xl border border-[#273449] bg-[#151D32] p-5 space-y-3.5 overflow-hidden",
        className
      )}
    >
      <div className="flex items-center justify-between pb-3 border-b border-[#273449]">
        <div className="h-5 w-32 animate-pulse rounded bg-slate-800" />
        <div className="h-4 w-20 animate-pulse rounded bg-slate-800" />
      </div>

      <div className="space-y-3 pt-2">
        {Array.from({ length: rows }).map((_, rIdx) => (
          <div
            key={rIdx}
            className="flex items-center gap-4 animate-pulse rounded-lg bg-[#0E1528] p-3 border border-slate-800/40"
          >
            {Array.from({ length: resolvedCols }).map((_, cIdx) => (
              <div
                key={cIdx}
                className={cn(
                  "h-4 rounded bg-slate-800",
                  cIdx === 0 ? "w-1/3" : "flex-1"
                )}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function CardSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="h-40 animate-pulse rounded-2xl border border-[#273449] bg-[#151D32] p-5 space-y-4"
        >
          <div className="h-5 w-1/2 rounded bg-slate-800" />
          <div className="h-4 w-3/4 rounded bg-slate-800" />
        </div>
      ))}
    </div>
  );
}
