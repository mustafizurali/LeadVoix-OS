"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: string;
  type?: "lead" | "deal" | "task" | "priority" | "agent" | "call" | "general";
  className?: string;
}

export function StatusBadge({ status, type = "general", className }: StatusBadgeProps) {
  const normalized = (status || "").toUpperCase();

  let styles = "bg-slate-800/60 text-[#AAB4CC] border-slate-700/60";
  let label = status || "Unknown";

  if (type === "lead" || normalized === "NEW" || normalized === "CONTACTED" || normalized === "QUALIFIED" || normalized === "CONVERTED" || normalized === "UNQUALIFIED") {
    switch (normalized) {
      case "NEW":
        styles = "bg-[#24C8D8]/15 text-[#24C8D8] border-[#24C8D8]/30";
        label = "New";
        break;
      case "CONTACTED":
        styles = "bg-[#7657F6]/15 text-[#7657F6] border-[#7657F6]/30";
        label = "Contacted";
        break;
      case "QUALIFIED":
        styles = "bg-[#35D6C1]/15 text-[#35D6C1] border-[#35D6C1]/30";
        label = "Qualified";
        break;
      case "CONVERTED":
        styles = "bg-purple-500/15 text-purple-300 border-purple-500/30";
        label = "Converted";
        break;
      case "UNQUALIFIED":
        styles = "bg-slate-700/40 text-slate-400 border-slate-700/50";
        label = "Unqualified";
        break;
    }
  } else if (type === "deal" || normalized === "OPEN" || normalized === "WON" || normalized === "LOST") {
    switch (normalized) {
      case "OPEN":
        styles = "bg-[#24C8D8]/15 text-[#24C8D8] border-[#24C8D8]/30";
        label = "Open";
        break;
      case "WON":
        styles = "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
        label = "Won";
        break;
      case "LOST":
        styles = "bg-red-500/15 text-red-400 border-red-500/30";
        label = "Lost";
        break;
    }
  } else if (type === "priority" || normalized === "LOW" || normalized === "MEDIUM" || normalized === "HIGH" || normalized === "URGENT") {
    switch (normalized) {
      case "LOW":
        styles = "bg-slate-700/30 text-slate-400 border-slate-700/40";
        label = "Low";
        break;
      case "MEDIUM":
        styles = "bg-[#24C8D8]/15 text-[#24C8D8] border-[#24C8D8]/30";
        label = "Medium";
        break;
      case "HIGH":
        styles = "bg-amber-500/15 text-amber-400 border-amber-500/30";
        label = "High";
        break;
      case "URGENT":
        styles = "bg-red-500/15 text-red-400 border-red-500/30 font-bold";
        label = "Urgent";
        break;
    }
  } else if (type === "task" || normalized === "TODO" || normalized === "IN_PROGRESS" || normalized === "DONE") {
    switch (normalized) {
      case "TODO":
        styles = "bg-slate-700/40 text-slate-300 border-slate-700/50";
        label = "To Do";
        break;
      case "IN_PROGRESS":
        styles = "bg-[#7657F6]/15 text-[#7657F6] border-[#7657F6]/30";
        label = "In Progress";
        break;
      case "DONE":
        styles = "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
        label = "Done";
        break;
    }
  } else if (type === "call" || ["COMPLETED", "IN-PROGRESS", "RINGING", "NO-ANSWER", "BUSY", "FAILED", "CANCELED"].includes(normalized)) {
    switch (normalized) {
      case "COMPLETED":
        styles = "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
        label = "Completed";
        break;
      case "IN-PROGRESS":
        styles = "bg-[#24C8D8]/15 text-[#24C8D8] border-[#24C8D8]/30";
        label = "In Progress";
        break;
      case "RINGING":
        styles = "bg-amber-500/15 text-amber-400 border-amber-500/30";
        label = "Ringing";
        break;
      case "NO-ANSWER":
        styles = "bg-slate-700/40 text-slate-400 border-slate-700/50";
        label = "No Answer";
        break;
      case "BUSY":
        styles = "bg-amber-500/15 text-amber-400 border-amber-500/30";
        label = "Busy";
        break;
      case "FAILED":
      case "CANCELED":
        styles = "bg-red-500/15 text-red-400 border-red-500/30";
        label = normalized === "FAILED" ? "Failed" : "Canceled";
        break;
    }
  }

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider select-none",
        styles,
        className
      )}
    >
      {label}
    </span>
  );
}
