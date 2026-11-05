"use client";

import React, { useState } from "react";
import { Laptop, Stethoscope, Wrench, Megaphone, Check, ArrowRight } from "lucide-react";

export default function EnterpriseUseCases() {
  const [activeTab, setActiveTab] = useState(0);

  const cases = [
    {
      id: "b2b",
      title: "B2B SaaS & Enterprise Sales",
      icon: Laptop,
      badge: "Inbound Pipeline",
      summary: "Qualify inbound prospects in seconds and eliminate the 24-hour lead response gap.",
      bullets: [
        "Answers inbound website callers with context-aware knowledge base scripts",
        "Evaluates seat counts, implementation timeline, and software budgets",
        "Directly provisions Lead records and assigns instant rep callbacks",
        "Advances high-intent prospects straight to Demo Scheduled stage",
      ],
      kpi: "Automated Lead & Deal Sync",
    },
    {
      id: "healthcare",
      title: "Healthcare & Specialized Clinics",
      icon: Stethoscope,
      badge: "Patient Intake",
      summary: "Provide 24/7 empathetic patient intake and intake scheduling without front-desk burnout.",
      bullets: [
        "Captures patient contact details, insurance provider, and reason for visit",
        "Triage calls based on urgency with immediate human escalation rules",
        "Schedules callback appointments directly in provider CRM queues",
        "Zero clinical advice given; strict adherence to intake boundaries",
      ],
      kpi: "Structured Patient Intake",
    },
    {
      id: "contractors",
      title: "Home Services & Field Ops",
      icon: Wrench,
      badge: "Emergency Dispatch",
      summary: "Never lose a high-value roofing, HVAC, or plumbing job to an unanswered ring.",
      bullets: [
        "Answers late-night emergency calls when field technicians are off-duty",
        "Logs job address, issue severity, and preferred service time window",
        "Creates emergency follow-up Tasks flagged with High Priority alerts",
        "Logs callback follow-up tasks with high priority alerts in CRM",
      ],
      kpi: "Priority Emergency Callback",
    },
    {
      id: "agencies",
      title: "Growth & Marketing Agencies",
      icon: Megaphone,
      badge: "White Label Retainers",
      summary: "Package autonomous voice-to-CRM automation as a high-margin monthly client retainer.",
      bullets: [
        "Set up dedicated voice numbers and custom intake prompts per client",
        "Prove tangible ROI by showing clients qualified leads delivered daily",
        "Multi-tenant isolation keeps every client's database cleanly partitioned",
        "Scale agency revenue without hiring offshore call center staff",
      ],
      kpi: "Multi-Client Isolation",
    },
  ];

  return (
    <section id="solutions" className="relative z-10 mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/10 pb-8">
        <div>
          <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#24C8D8]">
            INDUSTRY SCENARIOS
          </span>
          <h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-5xl">
            Engineered for High-Consequence Inbound Operations
          </h2>
        </div>
        <p className="max-w-md text-sm leading-relaxed text-slate-300">
          Tailored telephony intelligence tuned to the operational nuances of demanding industries.
        </p>
      </div>

      {/* Tabs and Display Grid */}
      <div className="mt-12 grid gap-8 lg:grid-cols-12">
        {/* Left: Tab Selectors */}
        <div className="lg:col-span-4 space-y-3">
          {cases.map((item, idx) => {
            const Icon = item.icon;
            const isSelected = activeTab === idx;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveTab(idx)}
                className={`w-full text-left rounded-xl p-4 transition border ${
                  isSelected
                    ? "border-[#7657F6] bg-[#151D32] shadow-lg"
                    : "border-white/5 bg-[#0E1424]/60 hover:bg-[#0E1424] text-slate-400"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2.5 font-bold text-sm text-white">
                    <Icon className={`h-4 w-4 ${isSelected ? "text-[#24C8D8]" : "text-slate-400"}`} />
                    <span>{item.title}</span>
                  </span>
                  <span className="font-mono text-[10px] text-slate-500 uppercase">
                    {item.badge}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Right: Detailed Scenario Deep Dive */}
        <div className="lg:col-span-8">
          <div className="rounded-2xl border border-white/15 bg-[#0E1424] p-7 sm:p-8 shadow-xl flex flex-col justify-between h-full">
            <div>
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <span className="font-mono text-xs uppercase tracking-wider text-[#24C8D8] font-bold">
                  {cases[activeTab].badge} WORKFLOW
                </span>
                <span className="rounded bg-emerald-500/15 px-2.5 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/30">
                  {cases[activeTab].kpi}
                </span>
              </div>

              <h3 className="mt-5 text-2xl font-black text-white">
                {cases[activeTab].title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-300">
                {cases[activeTab].summary}
              </p>

              <div className="mt-8 space-y-3.5">
                {cases[activeTab].bullets.map((bullet, i) => (
                  <div key={i} className="flex items-start gap-3 text-xs leading-relaxed text-slate-300">
                    <div className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-[#7657F6]/20 text-[#24C8D8]">
                      <Check className="h-3 w-3" />
                    </div>
                    <span>{bullet}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-white/10 flex items-center justify-between">
              <span className="text-xs text-slate-400">
                Ready to deploy for this use case?
              </span>
              <a
                href="#contact"
                className="inline-flex items-center gap-1.5 text-xs font-bold text-[#24C8D8] hover:underline"
              >
                <span>Schedule a Custom Script Walkthrough</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
