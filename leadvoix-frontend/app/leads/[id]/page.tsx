"use client";

import React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, User, Mail, Phone, Building2, PhoneCall, FileText, AlertCircle } from "lucide-react";

import DashboardLayout from "@/modules/dashboard/components/DashboardLayout";
import api from "@/lib/api/axios";
import { Lead } from "@/modules/leads/types/lead.types";
import { getLeadCalls } from "@/modules/leads/api/leadApi";
import { AgentCall } from "@/modules/agent-calls/types/agentCall.types";
import { PageContainer, PageHeader, StatusBadge } from "@/components/crm";
import { formatCallDuration } from "@/modules/dashboard/components/AgentAnalytics";

async function getLead(id: number): Promise<Lead> {
  const response = await api.get(`/leads/${id}`);
  return response.data;
}

export default function LeadDetailsPage() {
  const params = useParams();
  const leadId = Number(params?.id);

  const {
    data: lead,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["lead", leadId],
    queryFn: () => getLead(leadId),
    enabled: !!leadId,
  });

  const {
    data: leadCalls,
    isLoading: isLoadingCalls,
    isError: isCallsError,
  } = useQuery<AgentCall[]>({
    queryKey: ["lead-calls", leadId],
    queryFn: () => getLeadCalls(leadId),
    enabled: !!leadId,
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <PageContainer>
          <div className="rounded-2xl border border-[#273449] bg-[#151D32] p-8 animate-pulse space-y-4">
            <div className="h-6 w-48 rounded bg-slate-800" />
            <div className="h-4 w-96 rounded bg-slate-800" />
            <div className="grid grid-cols-3 gap-6 pt-6">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-16 rounded bg-[#0E1528]" />
              ))}
            </div>
          </div>
        </PageContainer>
      </DashboardLayout>
    );
  }

  if (isError || !lead) {
    return (
      <DashboardLayout>
        <PageContainer>
          <div className="flex flex-col items-center justify-center rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
            <AlertCircle className="h-8 w-8 text-red-400 mb-2" />
            <p className="text-sm font-semibold text-red-200">Failed to load lead record</p>
            <Link
              href="/leads"
              className="mt-4 rounded-lg bg-slate-800 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-700 transition-colors"
            >
              ← Back to Leads
            </Link>
          </div>
        </PageContainer>
      </DashboardLayout>
    );
  }

  const fullName = [lead.first_name, lead.last_name].filter(Boolean).join(" ") || "Prospect";

  return (
    <DashboardLayout>
      <PageContainer>
        <div className="flex items-center gap-2 mb-2">
          <Link
            href="/leads"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[#94A3B8] hover:text-[#24C8D8] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Leads</span>
          </Link>
        </div>

        <PageHeader
          title={fullName}
          subtitle="View lead details, notes, and AI telephone interaction history."
          actions={
            <StatusBadge status={lead.status} type="lead" className="text-xs px-3 py-1" />
          }
        />

        {/* Lead Information Card */}
        <section className="rounded-2xl border border-[#273449] bg-[#151D32] shadow-xl shadow-black/40 overflow-hidden">
          <div className="flex items-center gap-2.5 border-b border-[#273449] px-6 py-4">
            <User className="h-4 w-4 text-[#7657F6]" />
            <h2 className="text-base font-bold text-[#F5F7FC]">Lead Profile Information</h2>
          </div>

          <div className="grid gap-6 p-6 sm:grid-cols-2 lg:grid-cols-3 text-xs">
            <div className="space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#94A3B8]">Full Name</span>
              <p className="font-semibold text-sm text-[#F5F7FC]">{fullName}</p>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#94A3B8]">Email</span>
              <p className="font-medium text-sm text-[#F5F7FC] flex items-center gap-1.5">
                <Mail className="h-3.5 w-3.5 text-[#24C8D8]" />
                {lead.email || "—"}
              </p>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#94A3B8]">Phone</span>
              <p className="font-medium text-sm text-[#F5F7FC] flex items-center gap-1.5">
                <Phone className="h-3.5 w-3.5 text-[#35D6C1]" />
                {lead.phone || "—"}
              </p>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#94A3B8]">Company</span>
              <p className="font-medium text-sm text-[#F5F7FC] flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5 text-[#94A3B8]" />
                {lead.company || "—"}
              </p>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#94A3B8]">Source</span>
              <p className="font-medium text-sm text-[#F5F7FC]">{lead.source || "—"}</p>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#94A3B8]">Created Date</span>
              <p className="font-medium text-sm text-[#94A3B8]">
                {lead.created_at ? new Date(lead.created_at).toLocaleString() : "—"}
              </p>
            </div>
          </div>
        </section>

        {/* Lead Notes */}
        <section className="rounded-2xl border border-[#273449] bg-[#151D32] shadow-xl shadow-black/40 overflow-hidden">
          <div className="flex items-center gap-2.5 border-b border-[#273449] px-6 py-4">
            <FileText className="h-4 w-4 text-[#24C8D8]" />
            <h2 className="text-base font-bold text-[#F5F7FC]">Notes &amp; Context</h2>
          </div>
          <div className="p-6">
            <p className="whitespace-pre-wrap text-xs sm:text-sm leading-relaxed text-[#F5F7FC]/90 bg-[#0E1528] rounded-xl p-4 border border-[#273449]">
              {lead.notes || "No notes recorded for this lead yet."}
            </p>
          </div>
        </section>

        {/* Telephony Agent Calls History */}
        <section className="rounded-2xl border border-[#273449] bg-[#151D32] shadow-xl shadow-black/40 overflow-hidden">
          <div className="flex items-center justify-between border-b border-[#273449] px-6 py-4">
            <div className="flex items-center gap-2.5">
              <PhoneCall className="h-4 w-4 text-[#35D6C1]" />
              <div>
                <h2 className="text-base font-bold text-[#F5F7FC]">Voice Agent Calls</h2>
                <p className="text-xs text-[#94A3B8]">Call interactions linked to this prospect</p>
              </div>
            </div>
            {leadCalls && leadCalls.length > 0 && (
              <span className="rounded-full bg-[#35D6C1]/15 px-2.5 py-0.5 text-[11px] font-semibold text-[#35D6C1] border border-[#35D6C1]/30">
                {leadCalls.length} calls
              </span>
            )}
          </div>

          <div className="p-6">
            {isLoadingCalls ? (
              <p className="text-xs text-[#94A3B8]">Loading agent call history...</p>
            ) : isCallsError ? (
              <p className="text-xs text-red-400">Failed to load agent calls.</p>
            ) : !leadCalls || leadCalls.length === 0 ? (
              <div className="rounded-xl border border-dashed border-[#273449] bg-[#0E1528] p-6 text-center text-xs text-[#94A3B8]">
                No voice interactions logged for this lead yet.
              </div>
            ) : (
              <div className="space-y-3">
                {leadCalls.map((call) => (
                  <div
                    key={call.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-[#273449] bg-[#0E1528] p-4 transition-colors hover:border-slate-600"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-xs text-[#F5F7FC]">
                          Call #{call.id}
                        </span>
                        <StatusBadge status={call.status} type="call" />
                        <span className="text-[10px] text-[#94A3B8] uppercase">
                          {call.direction}
                        </span>
                      </div>
                      <p className="text-[11px] text-[#94A3B8]">
                        Caller: {call.caller_phone || "Unknown"} • {call.created_at ? new Date(call.created_at).toLocaleString() : ""}
                      </p>
                    </div>

                    <div className="flex items-center gap-4 text-xs">
                      <span className="text-[#94A3B8]">
                        Duration: <strong className="text-[#F5F7FC]">{formatCallDuration(call.duration || 0)}</strong>
                      </span>

                      {call.recording_url && (
                        <a
                          href={call.recording_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="rounded-lg border border-[#273449] bg-[#151D32] px-3 py-1 text-xs font-semibold text-[#24C8D8] hover:bg-slate-800 transition-colors"
                        >
                          Recording
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </PageContainer>
    </DashboardLayout>
  );
}
