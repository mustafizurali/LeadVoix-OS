"use client";

import React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  icon?: React.ComponentType<{ className?: string }>;
  loading?: boolean;
  size?: "sm" | "md" | "lg";
}

export function PrimaryButton({
  children,
  icon: Icon,
  loading = false,
  disabled = false,
  className,
  size = "md",
  ...props
}: ButtonProps) {
  const sizeStyles = {
    sm: "h-8 px-3 text-xs gap-1.5",
    md: "h-9 px-4 text-xs sm:text-sm gap-2",
    lg: "h-10 px-5 text-sm gap-2.5",
  };

  return (
    <button
      type="button"
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center rounded-lg bg-[#7657F6] font-semibold text-white shadow-md shadow-violet-950/40 transition-all hover:bg-[#6846ed] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#24C8D8] disabled:opacity-50 disabled:pointer-events-none cursor-pointer active:translate-y-px",
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin text-white" />
      ) : Icon ? (
        <Icon className="h-4 w-4" />
      ) : null}
      <span>{children}</span>
    </button>
  );
}

export function SecondaryButton({
  children,
  icon: Icon,
  loading = false,
  disabled = false,
  className,
  size = "md",
  ...props
}: ButtonProps) {
  const sizeStyles = {
    sm: "h-8 px-3 text-xs gap-1.5",
    md: "h-9 px-4 text-xs sm:text-sm gap-2",
    lg: "h-10 px-5 text-sm gap-2.5",
  };

  return (
    <button
      type="button"
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center rounded-lg border border-[#273449] bg-[#151D32] font-semibold text-[#F5F7FC] shadow-sm transition-all hover:bg-slate-800 hover:border-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#7657F6] disabled:opacity-50 disabled:pointer-events-none cursor-pointer active:translate-y-px",
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin text-[#AAB4CC]" />
      ) : Icon ? (
        <Icon className="h-4 w-4 text-[#AAB4CC]" />
      ) : null}
      <span>{children}</span>
    </button>
  );
}

export function DangerButton({
  children,
  icon: Icon,
  loading = false,
  disabled = false,
  className,
  size = "md",
  ...props
}: ButtonProps) {
  const sizeStyles = {
    sm: "h-8 px-3 text-xs gap-1.5",
    md: "h-9 px-4 text-xs sm:text-sm gap-2",
    lg: "h-10 px-5 text-sm gap-2.5",
  };

  return (
    <button
      type="button"
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center rounded-lg border border-red-500/30 bg-red-500/15 font-semibold text-red-300 shadow-sm transition-all hover:bg-red-500/25 hover:border-red-500/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 disabled:opacity-50 disabled:pointer-events-none cursor-pointer active:translate-y-px",
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin text-red-300" />
      ) : Icon ? (
        <Icon className="h-4 w-4" />
      ) : null}
      <span>{children}</span>
    </button>
  );
}
