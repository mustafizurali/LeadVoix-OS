"use client";

import React from "react";
import { Phone, Cpu, Database, ArrowRight } from "lucide-react";

export default function VoiceIntelligenceTimeline() {
  const phases = [
    {
      step: "01",
      title: "In-Call Telephony Streaming",
      subtitle: "Speech recognition & conversational audio stream",
      icon: Phone,
      color: "#24C8D8",
      points: [
        "Inbound call triggers Twilio webhook to conversational engine",
        "Bidirectional speech-to-text with conversational turn management",
        "Intent recognition evaluates customer budget, urgency, and requirements",
        "Deterministic human escalation procedure if off-script or requested",
      ],
    },
    {
      step: "02",
      title: "Post-Call Worker Lease",
      subtitle: "Dedicated persistent background job execution",
      icon: Cpu,
      color: "#7657F6",
      points: [
        "Post-call job enqueued in persistent PostgreSQL queue",
        "Independent worker claims job with atomic lease tokens and heartbeats",
        "Full transcript, call duration, and audio recording persisted to database",
        "Automated structured intelligence extraction and sentiment scoring",
      ],
    },
    {
      step: "03",
      title: "Deterministic CRM Mutation",
      subtitle: "Instant lead, task, and pipeline deal synchronization",
      icon: Database,
      color: "#10B981",
      points: [
        "Phone normalized into international E.164 format (+1XXXXXXXXXX)",
        "Deduplication against existing Contacts; creates or updates Lead record",
        "Follow-up Task automatically scheduled with priority and due dates",
        "CRM Deal created and advanced to Qualified Opportunity stage",
      ],
    },
  ];

  return (
    <section id="intelligence" className="relative z-10 mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
      {/* Header */}
      <div className="max-w-2xl">
        <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#24C8D8]">
          VOICE INTELLIGENCE ENGINE
        </span>
        <h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-5xl">
          The Anatomy of a Live Call
        </h2>
        <p className="mt-4 text-sm leading-relaxed text-slate-300">
          From incoming audio packet to closed revenue. See what happens behind the scenes during and after every conversation.
        </p>
      </div>

      {/* Timeline Layout */}
      <div className="mt-14 grid gap-8 lg:grid-cols-3">
        {phases.map((phase) => {
          const Icon = phase.icon;
          return (
            <div
              key={phase.step}
              className="relative rounded-2xl border border-white/10 bg-[#0E1424] p-6 lg:p-7 shadow-xl flex flex-col justify-between"
            >
              <div>
                {/* Step & Icon */}
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                  <span className="font-mono text-2xl font-black text-slate-500">
                    {phase.step}
                  </span>
                  <div
                    style={{ borderColor: `${phase.color}40`, backgroundColor: `${phase.color}15`, color: phase.color }}
                    className="flex h-10 w-10 items-center justify-center rounded-xl border"
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                </div>

                {/* Title */}
                <h3 className="mt-5 text-lg font-bold text-white">{phase.title}</h3>
                <p className="mt-1 text-xs text-slate-400">{phase.subtitle}</p>

                {/* Feature Points */}
                <ul className="mt-6 space-y-2.5 text-xs text-slate-300">
                  {phase.points.map((pt, i) => (
                    <li key={i} className="flex items-start gap-2 leading-relaxed">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-500" />
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Bottom State */}
              <div className="mt-8 pt-4 border-t border-white/5 flex items-center justify-between font-mono text-[11px] text-slate-400">
                <span>Phase Status</span>
                <span style={{ color: phase.color }} className="font-bold flex items-center gap-1">
                  <span>Operational</span>
                  <ArrowRight className="h-3 w-3" />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
