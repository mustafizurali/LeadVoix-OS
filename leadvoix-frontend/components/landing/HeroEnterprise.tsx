"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  Sparkles,
  CheckCircle2,
} from "lucide-react";

export default function HeroEnterprise() {
  return (
    <section className="relative z-10 overflow-hidden px-5 pt-8 pb-14 sm:pt-14 sm:pb-18 lg:px-8 lg:pt-16 lg:pb-20">
      <div className="mx-auto max-w-7xl">
        <div className="grid gap-8 lg:gap-10 xl:gap-12 lg:grid-cols-[1fr_1.14fr] lg:items-center">

          {/* ========================================================= */}
          {/* LEFT COLUMN: Narrative, Trial & CTAs                      */}
          {/* ========================================================= */}
          <div className="flex flex-col items-start text-left w-full">
            {/* Architectural Eyebrow Tag */}
            <div className="inline-flex max-w-full items-center gap-2 rounded-full border border-[#24C8D8]/30 bg-[#24C8D8]/10 px-3.5 py-1 font-mono text-[10px] sm:text-[11px] font-semibold uppercase tracking-[0.14em] text-[#24C8D8]">
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#24C8D8] animate-pulse" />
              <span className="truncate">AUTONOMOUS TELEPHONY // ENTERPRISE CRM AUTOMATION</span>
            </div>

            {/* Oversized Editorial Headline */}
            <h1 className="mt-5 text-[28px] sm:text-5xl lg:text-[42px] xl:text-[48px] font-black tracking-[-0.035em] text-white leading-[1.14] lg:leading-[1.12]">
              <span className="block sm:inline lg:block">Turn Every Inbound Call</span>{" "}
              <span className="block sm:inline lg:block">
                Into{" "}
                <span className="bg-gradient-to-r from-[#24C8D8] via-[#7657F6] to-[#a855f7] bg-clip-text text-transparent">
                  Qualified Pipeline.
                </span>
              </span>
            </h1>

            {/* Subheadline */}
            <p className="mt-4 sm:mt-5 max-w-xl text-base sm:text-lg leading-relaxed text-slate-300">
              Deploy autonomous AI voice agents that handle multi-turn customer calls, extract commercial intent, and commit structured Leads, follow-up Tasks, and Deals directly into your CRM as calls conclude.
            </p>

            {/* 7-DAY FREE TRIAL HIGHLIGHT BADGE */}
            <div className="mt-5 sm:mt-6 flex flex-col sm:flex-row items-start sm:items-center gap-3 rounded-xl border border-[#7657F6]/30 bg-[#7657F6]/10 p-3 sm:px-4 sm:py-2.5 max-w-xl">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#7657F6] text-white shadow-sm shrink-0">
                <Sparkles className="h-4 w-4" />
              </div>
              <div className="text-xs text-left">
                <span className="font-bold text-white">7-Day Free Trial Available: </span>
                <span className="text-slate-300">
                  30 calling minutes included • No credit card required • One trial per org • Zero automatic billing
                </span>
              </div>
            </div>

            {/* Dual CTAs for Direct SaaS */}
            <div className="mt-6 sm:mt-7 flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full sm:w-auto">
              <Link
                href="/signup"
                className="group inline-flex items-center justify-center gap-2 rounded-xl bg-[#7657F6] px-6 py-3.5 text-sm font-bold text-white shadow-xl shadow-[#7657F6]/30 transition hover:bg-[#6846ed]"
              >
                <span>Start 7-Day Free Trial</span>
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>

              <Link
                href="#contact"
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/[0.04] px-5 py-3.5 text-sm font-semibold text-slate-200 transition hover:border-[#24C8D8]/50 hover:bg-white/[0.08] hover:text-white"
              >
                <span>Book a Live Demo</span>
              </Link>
            </div>

            {/* Agency & White Label Switcher Link */}
            <div className="mt-3.5 flex items-center gap-2 text-xs text-slate-400">
              <span className="font-medium">Managing client accounts?</span>
              <Link
                href="#agency"
                className="font-semibold text-[#24C8D8] underline-offset-4 hover:underline flex items-center gap-1"
              >
                <span>Explore Agency & White Label Solutions</span>
                <span>→</span>
              </Link>
            </div>

            {/* Verifiable Architectural Indicators */}
            <div className="mt-6 sm:mt-7 w-full max-w-xl border-t border-white/10 pt-4 sm:pt-5">
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <div className="font-mono text-xs font-bold text-white sm:text-sm">
                    Twilio Webhook
                  </div>
                  <div className="mt-0.5 text-[10px] sm:text-[11px] text-slate-400">Audio Stream Ingest</div>
                </div>
                <div>
                  <div className="font-mono text-xs font-bold text-white sm:text-sm">
                    Tenant-Isolated
                  </div>
                  <div className="mt-0.5 text-[10px] sm:text-[11px] text-slate-400">PostgreSQL Boundary</div>
                </div>
                <div>
                  <div className="font-mono text-xs font-bold text-white sm:text-sm">
                    E.164 Standard
                  </div>
                  <div className="mt-0.5 text-[10px] sm:text-[11px] text-slate-400">Phone Normalization</div>
                </div>
              </div>
            </div>
          </div>

          {/* ========================================================= */}
          {/* RIGHT COLUMN: Genuine LeadVoix Dashboard Mockup           */}
          {/* ========================================================= */}
          <div className="relative w-full">
            {/* Ambient Lighting Behind Browser */}
            <div className="pointer-events-none absolute -inset-3 rounded-3xl bg-gradient-to-r from-[#7657F6]/25 via-[#24C8D8]/20 to-[#7657F6]/25 blur-2xl opacity-75" />

            {/* Browser Mockup Shell */}
            <div className="relative rounded-2xl border border-white/20 bg-[#0B1020] shadow-2xl overflow-hidden backdrop-blur-xl">

              {/* Browser Header Bar */}
              <div className="flex items-center justify-between border-b border-white/10 bg-[#070A12] px-3.5 py-2.5">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-rose-500/80" />
                  <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
                  <div className="ml-2 hidden sm:flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2.5 py-0.5 font-mono text-[10px] text-slate-400">
                    <span className="text-[#24C8D8]">https://</span>app.leadvoix.com/dashboard
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[9px] font-mono text-emerald-400 font-semibold">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span>AI Engine Active</span>
                  </span>
                  <span className="font-mono text-[9px] uppercase tracking-wider text-slate-500 hidden sm:inline">
                    Illustrative Demo
                  </span>
                </div>
              </div>

              {/* Genuine Dashboard Image */}
              <div className="relative w-full aspect-[16/10] overflow-hidden bg-[#0B1020]">
                <Image
                  src="/images/dashboard/leadvoix-dashboard-overview.png"
                  alt="Genuine LeadVoix Dashboard Interface — Real-time visibility across CRM pipelines, contact records, and voice agents"
                  fill
                  priority
                  sizes="(max-width: 768px) 100vw, (max-width: 1280px) 55vw, 750px"
                  className="object-cover object-top"
                />
              </div>

              {/* Bottom Caption Bar */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1 border-t border-white/10 bg-[#070A12]/95 px-4 py-2 text-[10px] text-slate-400 font-mono">
                <div className="flex items-center gap-1.5 truncate">
                  <CheckCircle2 className="h-3 w-3 text-[#24C8D8] shrink-0" />
                  <span className="text-slate-300 font-semibold">Genuine Platform View:</span>
                  <span className="truncate">LeadVoix OS Operational Cockpit</span>
                </div>
                <span className="text-slate-500 text-[9px]">
                  Illustrative Demo — Not Customer Data
                </span>
              </div>

            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
