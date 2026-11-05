"use client";

import React, { useState } from "react";
import Image from "next/image";
import {
  PhoneIncoming,
  Bot,
  FileSearch,
  UserCheck,
  CalendarCheck,
  TrendingUp,
  Clock,
  Database,
  CheckCircle2,
} from "lucide-react";

export default function InteractiveWorkflowEngine() {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      number: "01",
      title: "Incoming Call",
      timing: "Telephony Ring",
      icon: PhoneIncoming,
      accent: "#24C8D8",
      screenshot: "/images/dashboard/leadvoix-agent-calls.png",
      caption: "Genuine LeadVoix Agent Calls Interface — Call Ingest & Recording Audio Logs",
      explanation:
        "Customer dials your dedicated Twilio number. LeadVoix's webhook ingests caller ID, location, and initiates the conversational audio session.",
      details: [
        "Twilio webhook receives inbound call payload",
        "Cryptographic HMAC-SHA1 signature validation checks request authenticity",
        "Agent persona context loaded dynamically from organization database",
      ],
    },
    {
      number: "02",
      title: "AI Conversation",
      timing: "Active Stream",
      icon: Bot,
      accent: "#7657F6",
      screenshot: "/images/dashboard/leadvoix-agent-calls.png",
      caption: "Genuine LeadVoix Telephony Log Interface — Speech Turn-Taking & Call Duration",
      explanation:
        "The AI voice agent answers naturally, conducting multi-turn exchanges conditioned strictly on your company offerings and guardrails.",
      details: [
        "Natural speech recognition with conversational turn management",
        "Grounded in custom business knowledge base scripts",
        "Deterministic human escalation procedure if off-script or requested",
      ],
    },
    {
      number: "03",
      title: "Intent Extraction",
      timing: "Asynchronous Post-Call",
      icon: FileSearch,
      accent: "#38BDF8",
      screenshot: "/images/dashboard/leadvoix-dashboard-overview.png",
      caption: "Genuine LeadVoix Platform Cockpit — AI Intelligence & Summary Aggregation",
      explanation:
        "When the call concludes, our background worker asynchronously claims the job with atomic tokens to extract commercial intent and sentiment.",
      details: [
        "Post-call job claimed from persistent PostgreSQL queue with atomic lease fencing",
        "Evaluates caller urgency, objections, and commercial intent categories",
        "Generates concise call summary and persists full transcript to database",
      ],
    },
    {
      number: "04",
      title: "Lead Creation",
      timing: "Asynchronous Post-Call",
      icon: UserCheck,
      accent: "#10B981",
      screenshot: "/images/dashboard/leadvoix-crm-leads.png",
      caption: "Genuine LeadVoix CRM Leads Table — Automated Contact Normalization",
      explanation:
        "The worker normalizes the phone number to international E.164 format and creates or updates a Lead record inside your isolated organization.",
      details: [
        "Normalizes phone into E.164 format (+1XXXXXXXXXX) to prevent duplicate profiles",
        "Matches existing Contacts or automatically creates a new qualified Lead",
        "Strict organization-level tenant partitioning guarantees data isolation",
      ],
    },
    {
      number: "05",
      title: "Follow-up Task",
      timing: "Asynchronous Post-Call",
      icon: CalendarCheck,
      accent: "#F59E0B",
      screenshot: "/images/dashboard/leadvoix-tasks.png",
      caption: "Genuine LeadVoix Tasks Table — Automated Rep Action Item Dispatch",
      explanation:
        "Based on caller intent, a structured follow-up Task is automatically created with priority badges, deadlines, and assigned team members.",
      details: [
        "Schedules callback action items with high/medium/low priority tags",
        "Attaches conversation context and transcript link for assigned reps",
        "Immediately visible in CRM Tasks API and rep dashboards",
      ],
    },
    {
      number: "06",
      title: "Deal & Pipeline Update",
      timing: "Asynchronous Post-Call",
      icon: TrendingUp,
      accent: "#EC4899",
      screenshot: "/images/dashboard/leadvoix-deals-pipeline.png",
      caption: "Genuine LeadVoix Deals Board — Pipeline Stage Advancement & Value Tracking",
      explanation:
        "A commercial Deal is provisioned in your active CRM pipeline, advancing through defined stages and updating stage transition history.",
      details: [
        "Provisions Deal in default sales pipeline with estimated commercial value",
        "Advances deal to Qualified Opportunity stage based on call intelligence",
        "Appends immutable DealStageHistory records for conversion analytics",
      ],
    },
  ];

  const current = steps[activeStep];
  const CurrentIcon = current.icon;

  return (
    <section id="workflow" className="relative z-10 mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/10 pb-8">
        <div>
          <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#24C8D8]">
            REVENUE AUTOMATION PIPELINE
          </span>
          <h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-5xl">
            How a Phone Call Becomes Closed Revenue
          </h2>
        </div>
        <p className="max-w-md text-xs sm:text-sm leading-relaxed text-slate-300">
          From incoming audio to relational CRM mutations. Notice: Post-call intelligence and record updates execute asynchronously via dedicated background workers.
        </p>
      </div>

      {/* 6-Step Horizontal Progress Bar */}
      <div className="mt-10 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isSelected = activeStep === idx;
          return (
            <button
              key={step.number}
              type="button"
              onClick={() => setActiveStep(idx)}
              className={`rounded-xl border p-3.5 text-left transition-all duration-200 flex flex-col justify-between ${
                isSelected
                  ? "border-[#7657F6] bg-[#151D32] shadow-lg"
                  : "border-white/10 bg-[#0E1424]/60 hover:bg-[#0E1424] hover:border-white/20"
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="font-mono text-[10px] text-slate-500 font-bold">
                  {step.number}
                </span>
                <Icon
                  style={{ color: isSelected ? step.accent : "#94A3B8" }}
                  className="h-4 w-4"
                />
              </div>
              <div className="mt-2.5">
                <div className="text-xs font-bold text-white truncate">{step.title}</div>
                <div className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">{step.timing}</div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Step Detail and Real Product Screenshot Viewport */}
      <div className="mt-6 rounded-2xl border border-white/15 bg-[#0A0F1D] p-6 lg:p-8 shadow-2xl">
        <div className="grid gap-8 lg:grid-cols-12 lg:items-center">

          {/* Left Column: Architectural Step Description */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center gap-2">
              <span
                style={{ color: current.accent, backgroundColor: `${current.accent}15`, borderColor: `${current.accent}30` }}
                className="font-mono text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border flex items-center gap-1.5"
              >
                <Clock className="h-3 w-3" />
                <span>{current.timing}</span>
              </span>
              <span className="font-mono text-xs text-slate-400">Step {current.number} of 06</span>
            </div>

            <h3 className="text-2xl font-black text-white flex items-center gap-2.5">
              <CurrentIcon style={{ color: current.accent }} className="h-6 w-6" />
              <span>{current.title}</span>
            </h3>

            <p className="text-xs sm:text-sm leading-relaxed text-slate-300">
              {current.explanation}
            </p>

            <div className="space-y-2 pt-3 border-t border-white/10">
              {current.details.map((detail, i) => (
                <div key={i} className="flex items-start gap-2.5 text-xs text-slate-300 leading-relaxed">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{detail}</span>
                </div>
              ))}
            </div>

            <div className="pt-2 text-[11px] font-mono text-slate-400 flex items-center gap-2">
              <Database className="h-3.5 w-3.5 text-[#24C8D8]" />
              <span>Verified against backend worker implementation</span>
            </div>
          </div>

          {/* Right Column: Genuine Product Screenshot Preview */}
          <div className="lg:col-span-7">
            <div className="relative rounded-xl border border-white/15 bg-[#080C18] p-2 shadow-2xl overflow-hidden">
              <div className="flex items-center justify-between px-3 py-2 border-b border-white/10 bg-[#0E1424] rounded-t-lg text-[10px] text-slate-400 font-mono">
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <span>GENUINE PLATFORM EVIDENCE</span>
                </span>
                <span className="text-slate-500">Illustrative Demo — Not Customer Data</span>
              </div>
              <div className="relative w-full aspect-[16/10] overflow-hidden rounded-b-lg">
                <Image
                  src={current.screenshot}
                  alt={current.caption}
                  fill
                  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 60vw, 700px"
                  className="object-cover object-top transition-transform duration-300 hover:scale-[1.01]"
                  loading="lazy"
                />
              </div>
              <div className="mt-2 px-2 py-1 text-[10px] text-slate-400 font-mono text-center truncate">
                {current.caption}
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* Preload workflow screenshots for instantaneous client-side tab switching */}
      <div className="hidden pointer-events-none" aria-hidden="true">
        {steps.map((step) => (
          <Image
            key={step.number}
            src={step.screenshot}
            alt=""
            width={1}
            height={1}
            loading="lazy"
          />
        ))}
      </div>
    </section>
  );
}
