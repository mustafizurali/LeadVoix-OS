"use client";

import React from "react";
import { FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon = FolderOpen,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-2xl border border-[#273449] bg-[#151D32] p-8 sm:p-12 text-center",
        className
      )}
    >
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-[#273449] bg-[#0E1528] text-[#94A3B8] shadow-inner mb-4">
        <Icon className="h-7 w-7 text-[#7657F6]" />
      </div>
      <h3 className="text-base font-bold text-[#F5F7FC]">{title}</h3>
      {description && (
        <p className="mt-1.5 max-w-sm text-xs text-[#94A3B8] leading-relaxed">
          {description}
        </p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
