"use client";

import React from "react";
import Link from "next/link";
import { Check, Sparkles, ArrowRight, Building } from "lucide-react";

export default function EnterprisePricing() {
  return (
    <section id="pricing" className="relative z-10 mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
      {/* Header */}
      <div className="mx-auto max-w-3xl text-center">
        <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#7657F6]">
          TRANSPARENT PRICING
        </span>
        <h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-5xl">
          Predictable Telephony Investment
        </h2>
        <p className="mt-4 text-sm leading-relaxed text-slate-300">
          No hidden seat penalties. All plans include dedicated CRM pipelines, multi-tenant security, and transparent flat overage billing.
        </p>
      </div>

      {/* ========================================================= */}
      {/* 7-DAY FREE TRIAL HERO CARD                                */}
      {/* ========================================================= */}
      <div className="mt-12 overflow-hidden rounded-2xl border border-[#7657F6]/40 bg-gradient-to-r from-[#151D32] via-[#0E1528] to-[#121A30] p-6 sm:p-8 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-[#7657F6] text-white">
                <Sparkles className="h-3.5 w-3.5" />
              </span>
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#24C8D8]">
                RISK-FREE EVALUATION
              </span>
            </div>
            <h3 className="text-xl font-black text-white sm:text-2xl">
              7-Day Free Trial (30 Total Calling Minutes Included)
            </h3>
            <p className="max-w-2xl text-xs sm:text-sm leading-relaxed text-slate-300">
              Evaluate live AI voice calls and automatic CRM synchronization for your organization.
              Includes 30 calling minutes for up to 7 days. No credit card required, zero automatic billing, and no subscription commitment. (Automated backend quota enforcement is currently in roadmap development).
            </p>
          </div>

          <div className="shrink-0">
            <Link
              href="/signup"
              className="inline-flex items-center gap-2 rounded-xl bg-[#7657F6] px-6 py-3.5 text-xs sm:text-sm font-bold text-white shadow-lg shadow-[#7657F6]/30 transition hover:bg-[#6846ed]"
            >
              <span>Start 7-Day Free Trial</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* THREE DIRECT SAAS PRICING TIERS                           */}
      {/* ========================================================= */}
      <div className="mt-8 grid gap-8 lg:grid-cols-3">
        {/* Tier 1: Starter */}
        <div className="rounded-2xl border border-white/10 bg-[#0E1424] p-7 shadow-lg flex flex-col justify-between">
          <div>
            <div className="font-mono text-xs font-bold uppercase tracking-wider text-slate-400">
              STARTER
            </div>
            <h3 className="mt-1 text-xl font-bold text-white">Single Line Agent</h3>
            <p className="mt-2 text-xs text-slate-400">
              Ideal for small businesses automating their primary inbound phone line.
            </p>

            <div className="mt-6 flex items-baseline gap-1">
              <span className="text-4xl font-black text-white">
                $129
              </span>
              <span className="text-xs text-slate-400">/ month</span>
            </div>

            <ul className="mt-6 space-y-3 text-xs text-slate-300">
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span><strong>300 minutes</strong> included per month</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span><strong>1 active</strong> AI voice agent</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span>Dedicated Twilio local or toll-free number</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span>Core CRM Contacts, Leads, and Activity feed</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span>E.164 phone normalization & call logs</span>
              </li>
            </ul>
          </div>

          <div className="mt-8 pt-6 border-t border-white/10">
            <Link
              href="/signup"
              className="block w-full rounded-xl border border-white/15 bg-white/5 py-3 text-center text-xs font-bold text-white transition hover:bg-white/10"
            >
              Choose Starter
            </Link>
          </div>
        </div>

        {/* Tier 2: Professional (Featured) */}
        <div className="relative rounded-2xl border-2 border-[#7657F6] bg-[#12182B] p-7 shadow-2xl flex flex-col justify-between">
          <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-[#7657F6] px-3.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white shadow-sm">
            MOST POPULAR FOR GROWING TEAMS
          </div>

          <div>
            <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#c4b5fd]">
              PROFESSIONAL
            </div>
            <h3 className="mt-1 text-xl font-bold text-white">Full CRM Automation</h3>
            <p className="mt-2 text-xs text-slate-300">
              For teams requiring multi-agent routing and automated pipeline stages.
            </p>

            <div className="mt-6 flex items-baseline gap-1">
              <span className="text-4xl font-black text-white">
                $299
              </span>
              <span className="text-xs text-slate-400">/ month</span>
            </div>

            <ul className="mt-6 space-y-3 text-xs text-slate-300">
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span><strong>1,000 minutes</strong> included per month</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span><strong>3 active</strong> AI voice agents</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span>Automated Deals & Pipeline Stage advancement</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span>Automatic follow-up Task creation & assignment</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span>Custom knowledge base & human transfer routing</span>
              </li>
            </ul>
          </div>

          <div className="mt-8 pt-6 border-t border-white/10">
            <Link
              href="/signup"
              className="block w-full rounded-xl bg-[#7657F6] py-3 text-center text-xs font-bold text-white shadow-lg shadow-[#7657F6]/30 transition hover:bg-[#6846ed]"
            >
              Choose Professional
            </Link>
          </div>
        </div>

        {/* Tier 3: Scale (PRESERVE 10-AGENT LIMIT) */}
        <div className="rounded-2xl border border-white/10 bg-[#0E1424] p-7 shadow-lg flex flex-col justify-between">
          <div>
            <div className="font-mono text-xs font-bold uppercase tracking-wider text-slate-400">
              SCALE
            </div>
            <h3 className="mt-1 text-xl font-bold text-white">High-Volume Telephony</h3>
            <p className="mt-2 text-xs text-slate-400">
              For high-call-volume organizations running multiple department scripts.
            </p>

            <div className="mt-6 flex items-baseline gap-1">
              <span className="text-4xl font-black text-white">
                $699
              </span>
              <span className="text-xs text-slate-400">/ month</span>
            </div>

            <ul className="mt-6 space-y-3 text-xs text-slate-300">
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span><strong>2,500 minutes</strong> included per month</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span><strong>Up to 10 active</strong> AI voice agents</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span>Dedicated telephony routes & multi-agent routing</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span>Priority post-call worker queue processing</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="h-4 w-4 text-[#24C8D8] shrink-0" />
                <span>Advanced intent analytics & custom CRM webhooks</span>
              </li>
            </ul>
          </div>

          <div className="mt-8 pt-6 border-t border-white/10">
            <Link
              href="/signup"
              className="block w-full rounded-xl border border-white/15 bg-white/5 py-3 text-center text-xs font-bold text-white transition hover:bg-white/10"
            >
              Choose Scale
            </Link>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* FAIR OVERAGE & AGENCY PARTNER FLEET TIERS                 */}
      {/* ========================================================= */}
      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        {/* Fair Overage Guarantee */}
        <div className="rounded-xl border border-white/10 bg-[#0F1626] p-5 text-xs text-slate-300 flex items-center justify-between">
          <div>
            <div className="font-bold text-white text-sm">Transparent Overage Policy</div>
            <div className="mt-0.5 text-slate-400">
              Any usage beyond monthly plan allocation is billed at a flat <strong>$0.25 per minute</strong>. Zero surprise surcharges.
            </div>
          </div>
          <div className="font-mono text-base font-bold text-[#24C8D8] shrink-0 ml-4">
            $0.25/min
          </div>
        </div>

        {/* Agency Partner Program Tier Callout */}
        <div className="rounded-xl border border-[#24C8D8]/30 bg-[#0C1524] p-5 text-xs text-slate-300 flex items-center justify-between">
          <div>
            <div className="font-bold text-white text-sm flex items-center gap-1.5">
              <Building className="h-4 w-4 text-[#24C8D8]" />
              <span>Agency & Reseller Partner Fleet</span>
            </div>
            <div className="mt-0.5 text-slate-400">
              Manage multiple client organizations under one reseller agreement with pooled minutes and white-label early access.
            </div>
          </div>
          <Link
            href="#agency-inquiry"
            className="shrink-0 ml-4 rounded-lg bg-[#24C8D8]/15 border border-[#24C8D8]/30 px-3 py-1.5 font-bold text-[#24C8D8] hover:bg-[#24C8D8]/25"
          >
            Inquire
          </Link>
        </div>
      </div>
    </section>
  );
}
