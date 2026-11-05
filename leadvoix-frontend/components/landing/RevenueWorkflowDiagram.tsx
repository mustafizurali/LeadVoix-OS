"use client";

import React from "react";
import { PhoneIncoming, FileText, UserPlus, CalendarCheck, TrendingUp, ArrowRight } from "lucide-react";

export default function RevenueWorkflowDiagram() {
  const steps = [
    {
      step: "01",
      title: "Inbound Ring",
      schema: "AgentCall",
      desc: "Webhook execution captures caller ID, recording, and telephony stream.",
      icon: PhoneIncoming,
    },
    {
      step: "02",
      title: "Semantic Extraction",
      schema: "CallIntelligence",
      desc: "Worker extracts commercial intent, sentiment score, objection categories, and urgency.",
      icon: FileText,
    },
    {
      step: "03",
      title: "Lead Creation",
      schema: "Contact & Lead",
      desc: "Normalizes E.164 phone number, matches existing contacts or provisions new qualified Lead.",
      icon: UserPlus,
    },
    {
      step: "04",
      title: "Task Assignment",
      schema: "Task (Follow-up)",
      desc: "Schedules immediate rep action item with priority, callback deadline, and summary notes.",
      icon: CalendarCheck,
    },
    {
      step: "05",
      title: "Deal Advancement",
      schema: "Deal & PipelineStage",
      desc: "Creates commercial Deal in active pipeline, updates stage history, and projects revenue.",
      icon: TrendingUp,
    },
  ];

  return (
    <section id="workflow" className="relative z-10 mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/10 pb-8">
        <div>
          <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#7657F6]">
            REVENUE WORKFLOW
          </span>
          <h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-5xl">
            From Audio Waveform to Closed Deal
          </h2>
        </div>
        <p className="max-w-md text-sm leading-relaxed text-slate-300">
          Automate routine CRM post-call data entry. Each call triggers a structured 5-step revenue automation pipeline.
        </p>
      </div>

      {/* Horizontal Flow Container */}
      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {steps.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={item.step}
              className="relative rounded-2xl border border-white/10 bg-[#0E1424] p-5 shadow-lg flex flex-col justify-between group hover:border-[#7657F6]/50 transition"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-slate-500">
                    STEP {item.step}
                  </span>
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 text-[#24C8D8]">
                    <Icon className="h-4 w-4" />
                  </div>
                </div>

                <div className="mt-4 font-mono text-[10px] uppercase tracking-wider text-[#7657F6] font-semibold">
                  [{item.schema}]
                </div>
                <h3 className="mt-1 text-base font-bold text-white">{item.title}</h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-400">
                  {item.desc}
                </p>
              </div>

              {idx < steps.length - 1 && (
                <div className="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 z-20">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#151D32] border border-white/10 text-slate-400">
                    <ArrowRight className="h-3 w-3" />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
