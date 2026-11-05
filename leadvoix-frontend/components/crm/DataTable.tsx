"use client";

import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface DataTableProps {
  children: React.ReactNode;
  title?: string;
  countLabel?: string;
  total?: number;
  page?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  headerAction?: React.ReactNode;
  className?: string;
}

export function DataTable({
  children,
  title,
  countLabel,
  total,
  page,
  totalPages,
  onPageChange,
  headerAction,
  className,
}: DataTableProps) {
  return (
    <div
      className={cn(
        "flex flex-col rounded-2xl border border-[#273449] bg-[#151D32] shadow-xl shadow-black/40 overflow-hidden",
        className
      )}
    >
      {(title || countLabel || headerAction) && (
        <div className="flex items-center justify-between border-b border-[#273449] px-6 py-4">
          <div>
            {title && (
              <h2 className="text-base font-bold text-[#F5F7FC]">{title}</h2>
            )}
            {countLabel && (
              <p className="text-xs text-[#94A3B8]">{countLabel}</p>
            )}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}

      <div className="overflow-x-auto">{children}</div>

      {(total !== undefined || (totalPages && totalPages > 1)) && (
        <div className="flex items-center justify-between border-t border-[#273449] px-6 py-3.5 text-xs text-[#94A3B8]">
          <div>
            {total !== undefined && <span>Total: <strong className="text-[#F5F7FC]">{total}</strong> records</span>}
          </div>

          {totalPages && totalPages > 1 && onPageChange && page && (
            <div className="flex items-center gap-2">
              <span>
                Page <strong className="text-[#F5F7FC]">{page}</strong> of <strong className="text-[#F5F7FC]">{totalPages}</strong>
              </span>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => onPageChange(page - 1)}
                  className="rounded-lg border border-[#273449] p-1 text-[#94A3B8] hover:bg-slate-800 hover:text-white disabled:opacity-40 disabled:pointer-events-none"
                  aria-label="Previous page"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => onPageChange(page + 1)}
                  className="rounded-lg border border-[#273449] p-1 text-[#94A3B8] hover:bg-slate-800 hover:text-white disabled:opacity-40 disabled:pointer-events-none"
                  aria-label="Next page"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
