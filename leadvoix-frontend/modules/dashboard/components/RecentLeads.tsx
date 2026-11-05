"use client";

import React from "react";
import Link from "next/link";
import { ArrowUpRight, UserPlus, Mail, Phone, Building2, AlertCircle } from "lucide-react";
import { useLeads } from "@/modules/leads/hooks/useLeads";

export default function RecentLeads() {
  const { data, isLoading, isError, refetch } = useLeads({
    page: 1,
    limit: 5,
    sort_by: "created_at",
    order: "desc",
  });

  const leads = data?.items ?? [];

  const formatCreatedDate = (dateString: string) => {
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return "-";
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const getStatusBadge = (status: string) => {
    const normalized = (status || "").toUpperCase();

    switch (normalized) {
      case "NEW":
        return (
          <span className="inline-flex items-center rounded-md border border-[#24C8D8]/30 bg-[#24C8D8]/15 px-2 py-0.5 text-[11px] font-semibold text-[#24C8D8]">
            New
          </span>
        );
      case "CONTACTED":
        return (
          <span className="inline-flex items-center rounded-md border border-[#7657F6]/30 bg-[#7657F6]/15 px-2 py-0.5 text-[11px] font-semibold text-[#7657F6]">
            Contacted
          </span>
        );
      case "QUALIFIED":
        return (
          <span className="inline-flex items-center rounded-md border border-[#35D6C1]/30 bg-[#35D6C1]/15 px-2 py-0.5 text-[11px] font-semibold text-[#35D6C1]">
            Qualified
          </span>
        );
      case "CONVERTED":
        return (
          <span className="inline-flex items-center rounded-md border border-purple-500/30 bg-purple-500/15 px-2 py-0.5 text-[11px] font-semibold text-purple-300">
            Converted
          </span>
        );
      case "UNQUALIFIED":
        return (
          <span className="inline-flex items-center rounded-md border border-slate-700 bg-slate-800/60 px-2 py-0.5 text-[11px] font-semibold text-slate-400">
            Unqualified
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center rounded-md border border-slate-700 bg-slate-800/40 px-2 py-0.5 text-[11px] font-semibold text-[#AAB4CC]">
            {status || "Unknown"}
          </span>
        );
    }
  };

  return (
    <div className="flex h-full flex-col rounded-2xl border border-slate-800/80 bg-[#151D32] shadow-xl shadow-black/40 overflow-hidden">
      {/* Card Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#7657F6]/15 text-[#7657F6] border border-[#7657F6]/30">
            <UserPlus className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-[#F5F7FC]">Recent Leads</h2>
            <p className="text-xs text-[#AAB4CC]/70">Latest inbound prospects and AI conversions</p>
          </div>
        </div>

        <Link
          href="/leads"
          className="flex items-center gap-1 text-xs font-semibold text-[#24C8D8] transition-colors hover:text-[#52d7e6]"
        >
          <span>View all</span>
          <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="p-6 space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="flex items-center justify-between gap-4 animate-pulse rounded-lg bg-slate-900/50 p-3 border border-slate-800/40"
            >
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-slate-800" />
                <div className="space-y-1.5">
                  <div className="h-3.5 w-28 rounded bg-slate-800" />
                  <div className="h-2.5 w-40 rounded bg-slate-800" />
                </div>
              </div>
              <div className="h-5 w-16 rounded bg-slate-800" />
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <AlertCircle className="h-8 w-8 text-red-400 mb-2" />
          <p className="text-sm font-semibold text-red-200">Failed to load recent leads</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-3 rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && leads.length === 0 && (
        <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-800/60 text-[#AAB4CC] border border-slate-700/60 mb-3">
            <UserPlus className="h-6 w-6" />
          </div>
          <p className="text-sm font-bold text-[#F5F7FC]">No leads captured yet</p>
          <p className="mt-1 text-xs text-[#AAB4CC] max-w-xs">
            Start receiving prospects through web forms or configure an AI Voice Agent to qualify leads automatically.
          </p>
          <Link
            href="/leads"
            className="mt-4 rounded-lg bg-[#7657F6] px-3.5 py-1.5 text-xs font-semibold text-white shadow hover:bg-[#6846ed] transition-colors"
          >
            + Create First Lead
          </Link>
        </div>
      )}

      {/* Data Table */}
      {!isLoading && !isError && leads.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800/80 bg-slate-900/40 text-[11px] font-semibold uppercase tracking-wider text-[#AAB4CC]/70">
                <th className="px-6 py-3">Lead Contact</th>
                <th className="px-4 py-3">Company</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Captured</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {leads.map((lead) => {
                const fullName = [lead.first_name, lead.last_name].filter(Boolean).join(" ") || "Unnamed Lead";
                const initials = fullName
                  .split(" ")
                  .map((n) => n[0])
                  .slice(0, 2)
                  .join("")
                  .toUpperCase() || "L";

                return (
                  <tr
                    key={lead.id}
                    className="group transition-colors hover:bg-slate-800/40"
                  >
                    {/* Lead Contact Info */}
                    <td className="px-6 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-tr from-[#7657F6]/40 to-[#24C8D8]/30 font-bold text-white border border-slate-700">
                          {initials}
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-[#F5F7FC] truncate group-hover:text-[#24C8D8] transition-colors">
                            {fullName}
                          </p>
                          <div className="flex items-center gap-2 text-[11px] text-[#AAB4CC]/70">
                            {lead.email && (
                              <span className="flex items-center gap-1 truncate max-w-[140px]">
                                <Mail className="h-3 w-3 shrink-0" />
                                {lead.email}
                              </span>
                            )}
                            {lead.phone && !lead.email && (
                              <span className="flex items-center gap-1 truncate">
                                <Phone className="h-3 w-3 shrink-0" />
                                {lead.phone}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Company */}
                    <td className="px-4 py-3.5 text-[#F5F7FC]">
                      {lead.company ? (
                        <div className="flex items-center gap-1.5">
                          <Building2 className="h-3.5 w-3.5 text-[#AAB4CC]" />
                          <span className="truncate max-w-[120px]">{lead.company}</span>
                        </div>
                      ) : (
                        <span className="text-[#AAB4CC]/50">—</span>
                      )}
                    </td>

                    {/* Status */}
                    <td className="px-4 py-3.5">
                      {getStatusBadge(lead.status)}
                    </td>

                    {/* Created */}
                    <td className="px-4 py-3.5 text-[#AAB4CC]">
                      {formatCreatedDate(lead.created_at)}
                    </td>

                    {/* Action */}
                    <td className="px-6 py-3.5 text-right">
                      <Link
                        href={`/leads/${lead.id}`}
                        className="inline-flex items-center gap-1 rounded-md bg-slate-800/60 px-2.5 py-1 text-[11px] font-medium text-[#F5F7FC] transition-colors hover:bg-[#7657F6] hover:text-white"
                      >
                        <span>View</span>
                        <ArrowUpRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
