"use client";

import React, { useState } from "react";
import { Bot, CheckCircle2, ArrowRight } from "lucide-react";

export default function VoiceAgentPersonas() {
  const [activePersona, setActivePersona] = useState<number>(0);

  const personas = [
    {
      id: "receptionist",
      role: "Front-Desk Receptionist",
      name: "Clara",
      tagline: "24/7 Office Call Answering, Intake & Smart Transfer",
      accentColor: "#24C8D8",
      description:
        "Greets callers warmly, answers routine business inquiries using your custom knowledge base, and gracefully initiates human transfers when needed.",
      dialogue: [
        { speaker: "caller", text: "Hi, I need to check if Dr. Stevens has any availability this Thursday afternoon." },
        { speaker: "agent", text: "Dr. Stevens has an opening at 2:30 PM this Thursday. Would you like me to reserve that appointment for you?" },
        { speaker: "caller", text: "Yes please, 2:30 PM works perfectly." },
        { speaker: "agent", text: "You're all set for Thursday at 2:30 PM. I've logged your intake request and our front desk will send a confirmation." },
      ],
      capabilities: [
        "Answers inbound calls with zero hold-time delay",
        "Conditioned on your business hours, services & pricing FAQ",
        "Deterministic live transfer procedure to front desk if requested",
        "Captures caller contact details and logs intake notes in CRM",
      ],
      crmOutput: "Contact record created • Intake notes attached • Transfer logged",
    },
    {
      id: "sales-sdr",
      role: "Inbound Sales SDR",
      name: "Alex",
      tagline: "Commercial Qualification & Automated Deal Creation",
      accentColor: "#7657F6",
      description:
        "Engages high-intent website and advertising callers, evaluates software or service requirements, extracts budget/urgency, and provisions CRM deals.",
      dialogue: [
        { speaker: "caller", text: "We're shipping around 400 freight loads a month and our current dispatch software is failing." },
        { speaker: "agent", text: "Understood. LeadVoix easily handles that volume. Are you looking to migrate your system within the next 30 days?" },
        { speaker: "caller", text: "Yes, we need a solution deployed by next month." },
        { speaker: "agent", text: "Got it. I've qualified your requirements and scheduled a senior logistics specialist callback for tomorrow at 10 AM." },
      ],
      capabilities: [
        "Qualifies inbound commercial intent and project timeline",
        "Extracts estimated contract value and operational scale",
        "Creates Lead and advances Deal stage to Qualified Opportunity",
        "Dispatches high-priority callback task for account executives",
      ],
      crmOutput: "Lead #1042 created • Deal: $45k ARR • Priority follow-up task scheduled",
    },
    {
      id: "support-triage",
      role: "After-Hours Support & Dispatch",
      name: "Marcus",
      tagline: "Emergency Triage, Priority Alerts & On-Call Escalation",
      accentColor: "#38BDF8",
      description:
        "Handles critical off-hours calls for contractors, property managers, and healthcare clinics, triaging urgency and alerting on-call staff.",
      dialogue: [
        { speaker: "caller", text: "Our commercial refrigeration unit just lost power and we have inventory at risk." },
        { speaker: "agent", text: "I understand this is critical. What is the facility address and are any temperature alarms sounding?" },
        { speaker: "caller", text: "We're at 840 Industrial Blvd. The secondary compressor is offline." },
        { speaker: "agent", text: "I've flagged this as a Priority 1 emergency. An urgent notification task has been created for our on-call technician." },
      ],
      capabilities: [
        "Answers emergency calls after normal business hours",
        "Triages issue severity using structured diagnostic prompts",
        "Creates emergency follow-up Tasks flagged with High Priority",
        "Prepares full audio recording and transcript for field staff",
      ],
      crmOutput: "Urgent Task created • High Priority alert • Audio recording logged",
    },
  ];

  const current = personas[activePersona];

  return (
    <section id="personas" className="relative z-10 mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/10 pb-8">
        <div>
          <div className="inline-flex items-center gap-2 rounded border border-[#7657F6]/30 bg-[#7657F6]/10 px-3 py-1 font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-[#c4b5fd]">
            <Bot className="h-3.5 w-3.5 text-[#24C8D8]" />
            <span>SPECIALIZED AI VOICE PERSONAS</span>
          </div>
          <h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-5xl">
            Tuned for Your Specific Business Operations
          </h2>
        </div>
        <div className="text-right">
          <p className="max-w-md text-xs sm:text-sm leading-relaxed text-slate-300">
            Deploy specialized voice agents with tailored guardrails, business knowledge bases, and deterministic CRM workflows.
          </p>
          <span className="font-mono text-[10px] uppercase tracking-wider text-slate-500 mt-2 block">
            Illustrative Demo — Not Customer Data
          </span>
        </div>
      </div>

      {/* Persona Selection Tabs */}
      <div className="mt-8 grid gap-3 sm:grid-cols-3">
        {personas.map((persona, idx) => {
          const isSelected = activePersona === idx;
          return (
            <button
              key={persona.id}
              type="button"
              onClick={() => setActivePersona(idx)}
              className={`rounded-2xl border p-5 text-left transition-all duration-200 ${
                isSelected
                  ? "border-[#7657F6] bg-[#12182B] shadow-xl shadow-purple-950/20"
                  : "border-white/10 bg-[#0E1424]/60 hover:bg-[#0E1424] hover:border-white/20"
              }`}
            >
              <div className="flex items-center justify-between">
                <span
                  style={{ color: persona.accentColor }}
                  className="font-mono text-xs font-bold uppercase tracking-wider"
                >
                  {persona.role}
                </span>
                <span className="text-xs text-slate-400 font-mono">Agent: {persona.name}</span>
              </div>
              <h3 className="mt-2 text-base font-bold text-white">{persona.tagline}</h3>
            </button>
          );
        })}
      </div>

      {/* Active Persona Deep Dive Workbench */}
      <div className="mt-6 rounded-2xl border border-white/15 bg-[#0A0F1D] p-6 lg:p-8 shadow-2xl">
        <div className="grid gap-8 lg:grid-cols-12 lg:items-start">

          {/* Left Column: Dialogue Exchange Preview */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="font-mono text-xs font-bold text-white uppercase tracking-wider">
                  Simulated Conversational Exchange ({current.name})
                </span>
              </div>
              <span className="font-mono text-[9px] uppercase tracking-wider text-slate-500">
                Illustrative Demo — Not Customer Data
              </span>
            </div>

            {/* Conversation Script Bubbles */}
            <div className="space-y-3 rounded-xl border border-white/5 bg-[#070A12] p-4 text-xs">
              {current.dialogue.map((line, i) => (
                <div
                  key={i}
                  className={`flex flex-col ${line.speaker === "agent" ? "items-end" : "items-start"}`}
                >
                  <span className="font-mono text-[10px] text-slate-500 mb-1">
                    {line.speaker === "agent" ? `AI Agent (${current.name})` : "Caller"}
                  </span>
                  <div
                    className={`max-w-md rounded-xl p-3 leading-relaxed ${
                      line.speaker === "agent"
                        ? "bg-[#1A233D] text-[#F5F7FC] border border-[#7657F6]/30"
                        : "bg-white/5 text-slate-300 border border-white/5"
                    }`}
                  >
                    {line.text}
                  </div>
                </div>
              ))}
            </div>

            {/* CRM Automation Output Card */}
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                <span className="text-slate-300 font-medium">Automated CRM Result:</span>
                <strong className="text-white">{current.crmOutput}</strong>
              </div>
              <span className="font-mono text-[10px] text-emerald-400 uppercase tracking-wider">
                Post-Call Sync
              </span>
            </div>
          </div>

          {/* Right Column: Capabilities & Configuration */}
          <div className="lg:col-span-5 space-y-5">
            <div>
              <span
                style={{ color: current.accentColor }}
                className="font-mono text-xs font-bold uppercase tracking-wider"
              >
                Operational Scope
              </span>
              <h4 className="mt-1 text-xl font-bold text-white">{current.role}</h4>
              <p className="mt-2 text-xs leading-relaxed text-slate-300">
                {current.description}
              </p>
            </div>

            <div className="space-y-2.5 pt-4 border-t border-white/10">
              <span className="font-mono text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                Verified Platform Capabilities
              </span>
              {current.capabilities.map((cap, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-slate-300 leading-relaxed">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[#24C8D8]" />
                  <span>{cap}</span>
                </div>
              ))}
            </div>

            <div className="pt-4">
              <a
                href="#contact"
                className="inline-flex items-center gap-2 text-xs font-bold text-[#24C8D8] hover:text-[#52e4f2] transition"
              >
                <span>Deploy {current.name} for your organization</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
