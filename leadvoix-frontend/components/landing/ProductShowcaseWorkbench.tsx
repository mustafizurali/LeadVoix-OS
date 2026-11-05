"use client";

import React, { useState } from "react";
import { Bot, TrendingUp } from "lucide-react";

export default function ProductShowcaseWorkbench() {
  const [activeTab, setActiveTab] = useState<"pipeline" | "agent">("pipeline");

  return (
    <section id="product" className="relative z-10 mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
      {/* Editorial Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/10 pb-8">
        <div>
          <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#7657F6]">
            DUAL-ENGINE ARCHITECTURE
          </span>
          <h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-5xl">
            Telephony & CRM Operating in Real-Time Sync
          </h2>
        </div>
        <p className="max-w-md text-sm leading-relaxed text-slate-300">
          Most voice tools dump audio transcripts into email inboxes. LeadVoix directly mutates your relational CRM pipeline stages, contacts, and follow-up tasks.
        </p>
      </div>

      {/* Tab Switcher */}
      <div className="mt-8 flex items-center justify-between flex-wrap gap-4">
        <div className="inline-flex rounded-xl border border-white/10 bg-[#0D1322] p-1 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab("pipeline")}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 font-semibold transition ${
              activeTab === "pipeline"
                ? "bg-[#7657F6] text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <TrendingUp className="h-3.5 w-3.5" />
            <span>CRM Pipeline Automation</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("agent")}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 font-semibold transition ${
              activeTab === "agent"
                ? "bg-[#7657F6] text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Bot className="h-3.5 w-3.5" />
            <span>Voice Agent Telephony Studio</span>
          </button>
        </div>

        <span className="font-mono text-[10px] uppercase tracking-wider text-slate-500">
          [ILLUSTRATIVE PRODUCT WORKBENCH // DEMO DATA]
        </span>
      </div>

      {/* Workbench Container */}
      <div className="mt-6 overflow-hidden rounded-2xl border border-white/15 bg-[#0A0F1D] shadow-2xl">
        {activeTab === "pipeline" ? (
          /* ========================================================= */
          /* PANE A: Real-time Kanban Pipeline Board                   */
          /* ========================================================= */
          <div className="p-6 lg:p-8">
            <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-6">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>Enterprise Pipeline: North America Inbound</span>
                  <span className="rounded bg-white/10 px-2 py-0.5 text-[10px] font-mono text-slate-400 border border-white/10">
                    Illustrative Pipeline
                  </span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Automated stage advancement triggered directly by post-call worker evaluation.
                </p>
              </div>
              <div className="font-mono text-xs text-slate-300">
                Pipeline Value: <strong className="text-white">$318,000 ARR</strong>
              </div>
            </div>

            {/* Stage Columns */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {/* Column 1: Inbound Call Completed */}
              <div className="rounded-xl border border-white/10 bg-[#0F172A]/70 p-4">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-300 pb-2 border-b border-white/5">
                  <span>Inbound Audio</span>
                  <span className="font-mono text-[10px] text-slate-500">2 Calls</span>
                </div>
                <div className="mt-3 space-y-3">
                  <div className="rounded-lg border border-white/10 bg-[#151D32] p-3 text-xs shadow-sm">
                    <div className="font-bold text-white">Austin Solar Inc</div>
                    <div className="mt-1 text-[11px] text-slate-400">Caller: David Miller</div>
                    <div className="mt-2 flex items-center justify-between text-[10px]">
                      <span className="font-mono text-[#24C8D8]">Duration: 03m 12s</span>
                      <span className="text-emerald-400 font-semibold">$18,000</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Column 2: Qualified Lead (Automated) */}
              <div className="rounded-xl border border-[#7657F6]/40 bg-[#12182B] p-4 relative">
                <div className="flex items-center justify-between text-xs font-semibold text-[#c4b5fd] pb-2 border-b border-white/10">
                  <span className="flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#7657F6] animate-pulse" />
                    <span>Auto-Qualified</span>
                  </span>
                  <span className="font-mono text-[10px] text-slate-400">1 Lead</span>
                </div>
                <div className="mt-3 space-y-3">
                  <div className="rounded-lg border border-[#7657F6]/30 bg-[#151D32] p-3 text-xs shadow-md">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">Vance Logistics</span>
                      <span className="rounded bg-[#7657F6]/20 px-1.5 py-0.5 text-[9px] font-mono text-[#24C8D8]">
                        Score: 92
                      </span>
                    </div>
                    <div className="mt-1 text-[11px] text-slate-300">Marcus Vance • Fleet Ops</div>
                    <div className="mt-2 text-[10px] text-slate-400 border-t border-white/5 pt-1.5">
                      Auto-Task: Follow-up email sent
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[10px]">
                      <span className="font-mono text-[#24C8D8]">E.164: +14158902341</span>
                      <span className="text-emerald-400 font-bold">$45,000</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Column 3: Demo Scheduled */}
              <div className="rounded-xl border border-white/10 bg-[#0F172A]/70 p-4">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-300 pb-2 border-b border-white/5">
                  <span>Demo Scheduled</span>
                  <span className="font-mono text-[10px] text-slate-500">3 Deals</span>
                </div>
                <div className="mt-3 space-y-3">
                  <div className="rounded-lg border border-white/10 bg-[#151D32] p-3 text-xs shadow-sm">
                    <div className="font-bold text-white">Apex Medical Group</div>
                    <div className="mt-1 text-[11px] text-slate-400">Dr. Sarah Jenkins</div>
                    <div className="mt-2 flex items-center justify-between text-[10px]">
                      <span className="text-slate-400">Calendar: Friday 2 PM</span>
                      <span className="text-emerald-400 font-semibold">$85,000</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Column 4: Proposal / Closed Won */}
              <div className="rounded-xl border border-white/10 bg-[#0F172A]/70 p-4">
                <div className="flex items-center justify-between text-xs font-semibold text-emerald-400 pb-2 border-b border-white/5">
                  <span>Proposal & Won</span>
                  <span className="font-mono text-[10px] text-slate-500">2 Deals</span>
                </div>
                <div className="mt-3 space-y-3">
                  <div className="rounded-lg border border-emerald-500/20 bg-[#151D32] p-3 text-xs shadow-sm">
                    <div className="font-bold text-white">OmniCorp Industrial</div>
                    <div className="mt-1 text-[11px] text-slate-400">Annual Contract Signed</div>
                    <div className="mt-2 flex items-center justify-between text-[10px]">
                      <span className="text-emerald-400">Closed Won</span>
                      <span className="text-emerald-400 font-bold">$170,000</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* ========================================================= */
          /* PANE B: Autonomous Agent Telephony Studio                 */
          /* ========================================================= */
          <div className="p-6 lg:p-8">
            <div className="grid gap-8 lg:grid-cols-12">
              <div className="lg:col-span-5 space-y-4">
                <h3 className="text-base font-bold text-white">Agent Telephony Configuration</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Condition prompt behavior, telephony routing numbers, and deterministic fallback procedures for human escalation.
                </p>

                <div className="space-y-3 rounded-xl border border-white/10 bg-[#151D32] p-4 text-xs">
                  <div>
                    <label className="text-[10px] uppercase font-mono tracking-wider text-slate-400">Agent Persona</label>
                    <div className="mt-1 font-semibold text-white">Inbound Enterprise Sales Rep (Sarah)</div>
                  </div>
                  <div className="pt-2 border-t border-white/5">
                    <label className="text-[10px] uppercase font-mono tracking-wider text-slate-400">Assigned Twilio Number</label>
                    <div className="mt-1 font-mono text-[#24C8D8]">+1 (800) 492-9102</div>
                  </div>
                  <div className="pt-2 border-t border-white/5">
                    <label className="text-[10px] uppercase font-mono tracking-wider text-slate-400">Human Escalation Routing</label>
                    <div className="mt-1 text-slate-300">Transfers to Sales Desk: +1 (415) 555-0199</div>
                  </div>
                </div>
              </div>

              <div className="lg:col-span-7 space-y-3">
                <div className="text-xs font-bold text-slate-300 flex items-center justify-between">
                  <span>System Prompt & Commercial Guardrails</span>
                  <span className="font-mono text-[10px] text-slate-500">FastAPI Telephony Worker</span>
                </div>
                <div className="rounded-xl border border-white/10 bg-[#080C18] p-4 font-mono text-[11px] leading-relaxed text-slate-300 space-y-2">
                  <p className="text-slate-500">{"// Conditioned Business Knowledge & Action Rules"}</p>
                  <p className="text-[#24C8D8]">
                    {`You are an AI sales specialist for Vance Logistics. Greet callers professionally.`}
                  </p>
                  <p className="text-slate-300">
                    {`Identify: 1) Monthly shipment volume, 2) Timeline, 3) Current ERP system.`}
                  </p>
                  <p className="text-[#7657F6]">
                    {`If caller asks for a human rep or complex contractual quotes, politely trigger the transfer procedure to the designated sales escalation line.`}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
