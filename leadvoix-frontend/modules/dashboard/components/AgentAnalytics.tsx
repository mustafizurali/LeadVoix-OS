"use client";

import React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Bot,
  PhoneCall,
  CheckCircle2,
  PhoneForwarded,
  ArrowUpRight,
  Sparkles,
  Clock,
  AlertCircle,
} from "lucide-react";

import api from "@/lib/api/axios";
import { getAgentCalls } from "@/modules/agent-calls/api/agentCallApi";
import { AgentCall } from "@/modules/agent-calls/types/agentCall.types";
import { useBackendHealth } from "@/lib/hooks/useBackendHealth";
import { cn } from "@/lib/utils";

interface Agent {
  id: number;
  name: string;
  description: string | null;
  voice: string | null;
  language: string;
  is_active: boolean;
  organization_id: number;
}

interface AgentPerformanceMetric {
  agent: Agent;
  totalCalls: number;
  answeredCalls: number;
  completedCalls: number;
  answerRate: number;
  formattedAvgDuration: string;
}

export function formatCallDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return "—";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins > 0) {
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  }
  return `${secs}s`;
}

// Backend status semantics: a call was answered if started_at is present, duration > 0, or status is in-progress/completed
function isCallAnswered(call: AgentCall): boolean {
  if (call.started_at !== null) return true;
  if (typeof call.duration === "number" && call.duration > 0) return true;
  return call.status === "in-progress" || call.status === "completed";
}

export default function AgentAnalytics() {
  const { data: isBackendOnline, isLoading: healthLoading } = useBackendHealth();

  // 1. Fetch real agents for current user's organization
  const { data: agents = [], isLoading: agentsLoading } = useQuery<Agent[]>({
    queryKey: ["dashboard-agents"],
    queryFn: async () => {
      const response = await api.get("/agents");
      return response.data;
    },
  });

  // 2. Fetch calls for all agents in parallel
  const { data: analytics, isLoading: callsLoading } = useQuery({
    queryKey: ["dashboard-agent-calls", agents.map((a) => a.id)],
    queryFn: async () => {
      if (agents.length === 0) {
        return {
          totalCalls: 0,
          answeredCalls: 0,
          completedCalls: 0,
          answerRate: 0,
          avgDurationSec: 0,
          formattedAvgDuration: "—",
          performance: [] as AgentPerformanceMetric[],
        };
      }

      // Fetch calls for each agent
      const callResults = await Promise.all(
        agents.map(async (agent) => {
          try {
            const calls: AgentCall[] = await getAgentCalls(agent.id);
            return { agent, calls: Array.isArray(calls) ? calls : [] };
          } catch {
            return { agent, calls: [] as AgentCall[] };
          }
        })
      );

      let totalCalls = 0;
      let answeredCalls = 0;
      let completedCalls = 0;
      let totalDuration = 0;
      let callsWithDurationCount = 0;
      const performance: AgentPerformanceMetric[] = [];

      for (const { agent, calls } of callResults) {
        const agentTotal = calls.length;
        const agentAnswered = calls.filter(isCallAnswered).length;
        const agentCompleted = calls.filter((c) => c.status === "completed").length;

        const agentCallsWithDuration = calls.filter(
          (c) => typeof c.duration === "number" && c.duration > 0
        );
        const agentDuration = agentCallsWithDuration.reduce(
          (sum, c) => sum + (c.duration || 0),
          0
        );
        const agentAvgSec =
          agentCallsWithDuration.length > 0
            ? Math.round(agentDuration / agentCallsWithDuration.length)
            : 0;

        totalCalls += agentTotal;
        answeredCalls += agentAnswered;
        completedCalls += agentCompleted;
        totalDuration += agentDuration;
        callsWithDurationCount += agentCallsWithDuration.length;

        performance.push({
          agent,
          totalCalls: agentTotal,
          answeredCalls: agentAnswered,
          completedCalls: agentCompleted,
          answerRate:
            agentTotal > 0 ? Math.round((agentAnswered / agentTotal) * 100) : 0,
          formattedAvgDuration: formatCallDuration(agentAvgSec),
        });
      }

      const answerRate =
        totalCalls > 0 ? Math.round((answeredCalls / totalCalls) * 100) : 0;
      const avgDurationSec =
        callsWithDurationCount > 0
          ? Math.round(totalDuration / callsWithDurationCount)
          : 0;

      return {
        totalCalls,
        answeredCalls,
        completedCalls,
        answerRate,
        avgDurationSec,
        formattedAvgDuration: formatCallDuration(avgDurationSec),
        performance,
      };
    },
    enabled: !agentsLoading,
  });

  const isLoading = agentsLoading || callsLoading;

  return (
    <div className="rounded-2xl border border-[#273449] bg-[#151D32] shadow-xl shadow-black/40 overflow-hidden">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#273449] px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#7657F6]/20 to-[#24C8D8]/20 border border-[#7657F6]/30 text-[#7657F6]">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-[#F5F7FC]">
                AI Voice Agent Intelligence
              </h2>
              {/* Real Telephony / Backend Health Status */}
              {healthLoading ? (
                <span className="flex items-center gap-1 rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-[#94A3B8] border border-slate-700">
                  Checking Telephony...
                </span>
              ) : isBackendOnline ? (
                <span className="flex items-center gap-1 rounded-full bg-[#24C8D8]/15 px-2 py-0.5 text-[10px] font-bold text-[#24C8D8] border border-[#24C8D8]/30 uppercase">
                  <Sparkles className="h-2.5 w-2.5" />
                  Telephony Online
                </span>
              ) : (
                <span className="flex items-center gap-1 rounded-full bg-red-500/15 px-2 py-0.5 text-[10px] font-bold text-red-400 border border-red-500/30 uppercase">
                  <AlertCircle className="h-2.5 w-2.5" />
                  Telephony Offline
                </span>
              )}
            </div>
            <p className="text-xs text-[#94A3B8]">
              Real-time operational statistics from autonomous Twilio voice agents
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/agents"
            className="rounded-lg border border-[#273449] bg-[#0E1528] px-3 py-1.5 text-xs font-semibold text-[#F5F7FC] transition-colors hover:bg-slate-800"
          >
            Manage Agents
          </Link>
          <Link
            href="/agent-calls"
            className="flex items-center gap-1 rounded-lg bg-[#7657F6] px-3 py-1.5 text-xs font-semibold text-white shadow transition-colors hover:bg-[#6846ed]"
          >
            <span>Call Logs</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="p-6 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="h-20 animate-pulse rounded-xl bg-[#0E1528] border border-[#273449] p-4"
              />
            ))}
          </div>
          <div className="h-28 animate-pulse rounded-xl bg-[#0E1528] border border-[#273449]" />
        </div>
      )}

      {/* Empty State: No Agents Configured */}
      {!isLoading && agents.length === 0 && (
        <div className="flex flex-col items-center justify-center p-8 sm:p-10 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#7657F6]/20 to-[#24C8D8]/10 border border-[#7657F6]/30 text-[#7657F6] mb-3 shadow-lg shadow-violet-950/30">
            <Bot className="h-7 w-7" />
          </div>
          <h3 className="text-base font-bold text-[#F5F7FC]">
            No AI Voice Agents Deployed
          </h3>
          <p className="mt-1.5 max-w-md text-xs text-[#94A3B8] leading-relaxed">
            LeadVoix OS allows autonomous voice agents to qualify incoming leads, capture meeting requests, and update CRM records automatically.
          </p>
          <div className="mt-5 flex gap-3">
            <Link
              href="/agents"
              className="rounded-lg bg-[#7657F6] px-4 py-2 text-xs font-semibold text-white shadow-md shadow-violet-950/40 hover:bg-[#6846ed] transition-colors"
            >
              + Create First Voice Agent
            </Link>
          </div>
        </div>
      )}

      {/* Active State with Real Metrics */}
      {!isLoading && agents.length > 0 && (
        <div className="p-6 space-y-6">
          {/* Top 4 Metrics */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Total Calls */}
            <div className="rounded-xl border border-[#273449] bg-[#0E1528] p-4 transition-colors hover:border-slate-600">
              <div className="flex items-center justify-between text-[#94A3B8]">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Total Calls
                </span>
                <PhoneCall className="h-4 w-4 text-[#7657F6]" />
              </div>
              <p className="mt-2 text-2xl font-extrabold text-[#F5F7FC]">
                {analytics?.totalCalls ?? 0}
              </p>
              <p className="mt-1 text-[11px] text-[#94A3B8]">
                Logged across all active agents
              </p>
            </div>

            {/* Answered Calls */}
            <div className="rounded-xl border border-[#273449] bg-[#0E1528] p-4 transition-colors hover:border-slate-600">
              <div className="flex items-center justify-between text-[#94A3B8]">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Answered Calls
                </span>
                <PhoneForwarded className="h-4 w-4 text-[#24C8D8]" />
              </div>
              <p className="mt-2 text-2xl font-extrabold text-[#F5F7FC]">
                {analytics?.answeredCalls ?? 0}
              </p>
              <p className="mt-1 text-[11px] text-[#94A3B8]">
                Connected customer interactions
              </p>
            </div>

            {/* Answer Rate */}
            <div className="rounded-xl border border-[#273449] bg-[#0E1528] p-4 transition-colors hover:border-slate-600">
              <div className="flex items-center justify-between text-[#94A3B8]">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Answer Rate
                </span>
                <CheckCircle2 className="h-4 w-4 text-[#35D6C1]" />
              </div>
              <p className="mt-2 text-2xl font-extrabold text-[#F5F7FC]">
                {analytics?.answerRate ?? 0}%
              </p>
              <p className="mt-1 text-[11px] text-[#94A3B8]">
                Answered vs total initiated
              </p>
            </div>

            {/* Average Duration (Formatted: e.g. 1m 24s) */}
            <div className="rounded-xl border border-[#273449] bg-[#0E1528] p-4 transition-colors hover:border-slate-600">
              <div className="flex items-center justify-between text-[#94A3B8]">
                <span className="text-xs font-semibold uppercase tracking-wider">
                  Avg Duration
                </span>
                <Clock className="h-4 w-4 text-amber-400" />
              </div>
              <p className="mt-2 text-2xl font-extrabold text-[#F5F7FC]">
                {analytics?.formattedAvgDuration ?? "—"}
              </p>
              <p className="mt-1 text-[11px] text-[#94A3B8]">
                Per connected conversation
              </p>
            </div>
          </div>

          {/* Agent Performance List */}
          <div>
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
                Agent Performance ({agents.length} configured)
              </h3>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {analytics?.performance.map(
                ({
                  agent,
                  totalCalls,
                  answeredCalls,
                  answerRate,
                  formattedAvgDuration,
                }) => (
                  <div
                    key={agent.id}
                    className="rounded-xl border border-[#273449] bg-[#0E1528] p-4 transition-all hover:border-slate-600 hover:bg-slate-900/70"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#7657F6]/20 text-[#7657F6] border border-[#7657F6]/30">
                          <Bot className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="font-semibold text-xs text-[#F5F7FC] truncate max-w-[150px]">
                            {agent.name}
                          </p>
                          <p className="text-[10px] text-[#94A3B8]">
                            {agent.voice || "Default Voice"} •{" "}
                            {agent.language?.toUpperCase() || "EN"}
                          </p>
                        </div>
                      </div>

                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase",
                          agent.is_active
                            ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                            : "bg-slate-700/30 text-slate-400 border border-slate-700/40"
                        )}
                      >
                        {agent.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>

                    <div className="mt-3 flex items-center justify-between border-t border-[#273449] pt-2 text-[11px] text-[#94A3B8]">
                      <span>
                        Calls: <strong className="text-[#F5F7FC]">{totalCalls}</strong>
                      </span>
                      <span>
                        Answered:{" "}
                        <strong className="text-[#35D6C1]">{answeredCalls}</strong>
                      </span>
                      <span>
                        Rate:{" "}
                        <strong className="text-[#24C8D8]">{answerRate}%</strong>
                      </span>
                    </div>

                    <div className="mt-1 text-[10px] text-[#94A3B8] text-right">
                      Avg Call: {formattedAvgDuration}
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
