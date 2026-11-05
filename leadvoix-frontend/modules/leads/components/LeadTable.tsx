"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Edit, Trash2, Mail, Phone, Building2, UserPlus, AlertCircle } from "lucide-react";

import { useLeads } from "../hooks/useLeads";
import { Lead } from "../types/lead.types";
import { DataTable, StatusBadge, TableSkeleton, EmptyState } from "@/components/crm";

interface LeadTableProps {
  search: string;
  onEditLead: (lead: Lead) => void;
  onDeleteLead: (lead: Lead) => void;
  onCreateLead?: () => void;
}

export default function LeadTable({
  search,
  onEditLead,
  onDeleteLead,
  onCreateLead,
}: LeadTableProps) {
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useLeads({
    search,
    page,
    limit: 10,
    sort_by: "created_at",
    order: "desc",
  });

  const leads = data?.items ?? [];

  if (isLoading) {
    return <TableSkeleton rows={6} columns={6} />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
        <AlertCircle className="h-8 w-8 text-red-400 mb-2" />
        <p className="text-sm font-semibold text-red-200">Failed to load leads</p>
        <p className="mt-1 text-xs text-red-300/80">Could not connect to the LeadVoix CRM database.</p>
        <button
          type="button"
          onClick={() => refetch()}
          className="mt-4 rounded-lg bg-red-500/20 px-3.5 py-1.5 text-xs font-semibold text-red-300 hover:bg-red-500/30 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (leads.length === 0) {
    return (
      <EmptyState
        icon={UserPlus}
        title={search ? "No matching leads found" : "No leads in your CRM"}
        description={
          search
            ? `No records matched your search query "${search}". Try clearing your filters.`
            : "Capture prospective customers and qualify inbound sales automatically with AI."
        }
        action={
          onCreateLead ? (
            <button
              type="button"
              onClick={onCreateLead}
              className="rounded-lg bg-[#7657F6] px-4 py-2 text-xs font-semibold text-white shadow hover:bg-[#6846ed] transition-colors"
            >
              + Create Lead
            </button>
          ) : undefined
        }
      />
    );
  }

  return (
    <DataTable
      title="All Leads"
      countLabel={`${leads.length} records shown`}
      total={data?.total}
      page={data?.page}
      totalPages={data?.total_pages}
      onPageChange={setPage}
    >
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-[#273449] bg-[#0E1528] text-[11px] font-semibold uppercase tracking-wider text-[#94A3B8]">
            <th className="px-6 py-3.5">Lead Contact</th>
            <th className="px-4 py-3.5">Company</th>
            <th className="px-4 py-3.5">Status</th>
            <th className="px-4 py-3.5">Source</th>
            <th className="px-4 py-3.5">Captured</th>
            <th className="px-6 py-3.5 text-right">Actions</th>
          </tr>
        </thead>

        <tbody className="divide-y divide-[#273449]">
          {leads.map((lead) => {
            const fullName = [lead.first_name, lead.last_name].filter(Boolean).join(" ") || "Prospect";
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
                {/* Contact Column */}
                <td className="px-6 py-3.5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-tr from-[#7657F6]/40 to-[#24C8D8]/30 font-bold text-white border border-[#273449]">
                      {initials}
                    </div>
                    <div className="min-w-0">
                      <Link
                        href={`/leads/${lead.id}`}
                        className="font-semibold text-[#F5F7FC] truncate group-hover:text-[#24C8D8] transition-colors hover:underline block"
                      >
                        {fullName}
                      </Link>
                      <div className="flex items-center gap-2 text-[11px] text-[#94A3B8]">
                        {lead.email && (
                          <span className="flex items-center gap-1 truncate max-w-[150px]">
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
                      <Building2 className="h-3.5 w-3.5 text-[#94A3B8]" />
                      <span className="truncate max-w-[140px]">{lead.company}</span>
                    </div>
                  ) : (
                    <span className="text-[#94A3B8]/50">—</span>
                  )}
                </td>

                {/* Status */}
                <td className="px-4 py-3.5">
                  <StatusBadge status={lead.status} type="lead" />
                </td>

                {/* Source */}
                <td className="px-4 py-3.5 text-[#94A3B8]">
                  {lead.source || "—"}
                </td>

                {/* Created */}
                <td className="px-4 py-3.5 text-[#94A3B8]">
                  {lead.created_at ? new Date(lead.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—"}
                </td>

                {/* Actions */}
                <td className="px-6 py-3.5 text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <Link
                      href={`/leads/${lead.id}`}
                      className="rounded-lg p-1.5 text-[#94A3B8] transition-colors hover:bg-slate-800 hover:text-white"
                      title="View Lead Details"
                    >
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>

                    <button
                      type="button"
                      onClick={() => onEditLead(lead)}
                      className="rounded-lg p-1.5 text-[#94A3B8] transition-colors hover:bg-slate-800 hover:text-[#24C8D8]"
                      title="Edit Lead"
                    >
                      <Edit className="h-3.5 w-3.5" />
                    </button>

                    <button
                      type="button"
                      onClick={() => onDeleteLead(lead)}
                      className="rounded-lg p-1.5 text-[#94A3B8] transition-colors hover:bg-red-500/15 hover:text-red-400"
                      title="Delete Lead"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </DataTable>
  );
}
