"use client";

import React from "react";
import Link from "next/link";
import {
  Layers,
  Building,
  Globe,
  Sliders,
  Sparkles,
  ArrowRight,
} from "lucide-react";

export default function AgencyWhiteLabelSection() {
  return (
    <section id="agency" className="relative z-10 border-y border-white/10 bg-[#0A0E1A] py-20 lg:py-28">
      <div className="mx-auto max-w-7xl px-5 lg:px-8">

        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/10 pb-8">
          <div>
            <div className="inline-flex items-center gap-2 rounded border border-[#24C8D8]/30 bg-[#24C8D8]/10 px-3 py-1 font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-[#24C8D8]">
              <Sparkles className="h-3 w-3" />
              <span>AGENCY & RESELLER ECOSYSTEM</span>
            </div>
            <h2 className="mt-4 text-3xl font-black tracking-tight text-white sm:text-5xl">
              Deliver Autonomous Voice-to-CRM Under Your Own Brand
            </h2>
          </div>
          <p className="max-w-md text-sm leading-relaxed text-slate-300">
            Build recurring high-margin monthly retainers. Manage multiple client organizations, deploy tailored voice agents, and deliver automated pipeline outcomes.
          </p>
        </div>

        {/* 2-Column Asymmetric Layout */}
        <div className="mt-12 grid gap-10 lg:grid-cols-12 lg:items-center">

          {/* Left Column: 4 Architecture Feature Pillars */}
          <div className="lg:col-span-6 space-y-6">

            {/* 1. Multi-Client Org Management (Live) */}
            <div className="rounded-2xl border border-white/10 bg-[#0F1626] p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#24C8D8]/10 text-[#24C8D8] border border-[#24C8D8]/30">
                    <Building className="h-4 w-4" />
                  </div>
                  <h3 className="text-base font-bold text-white">Multi-Client Organization Management</h3>
                </div>
                <span className="rounded bg-emerald-500/15 px-2 py-0.5 font-mono text-[10px] font-bold text-emerald-400 border border-emerald-500/30">
                  LIVE IN PLATFORM
                </span>
              </div>
              <p className="mt-3 text-xs leading-relaxed text-slate-300">
                Independent organization workspaces with tenant-level database isolation. Client leads, recordings, pipelines, and activities are partitioned cleanly by organization boundary.
              </p>
            </div>

            {/* 2. White-Label Client Workspaces (Roadmap) */}
            <div className="rounded-2xl border border-[#7657F6]/30 bg-[#0F1626] p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#7657F6]/15 text-[#7657F6] border border-[#7657F6]/30">
                    <Layers className="h-4 w-4" />
                  </div>
                  <h3 className="text-base font-bold text-white">White-Label Client Workspaces</h3>
                </div>
                <span className="rounded bg-[#7657F6]/20 px-2 py-0.5 font-mono text-[10px] font-bold text-[#c4b5fd] border border-[#7657F6]/40">
                  PARTNER ROADMAP
                </span>
              </div>
              <p className="mt-3 text-xs leading-relaxed text-slate-300">
                Replace LeadVoix branding with your agency logo, primary brand color system, and customized client portal interface for your end customers.
              </p>
            </div>

            {/* 3. Custom Domain & CNAME Mapping (Roadmap) */}
            <div className="rounded-2xl border border-white/10 bg-[#0F1626] p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#24C8D8]/10 text-[#24C8D8] border border-[#24C8D8]/30">
                    <Globe className="h-4 w-4" />
                  </div>
                  <h3 className="text-base font-bold text-white">Custom Domain & CNAME Mapping</h3>
                </div>
                <span className="rounded bg-[#7657F6]/20 px-2 py-0.5 font-mono text-[10px] font-bold text-[#c4b5fd] border border-[#7657F6]/40">
                  PARTNER ROADMAP
                </span>
              </div>
              <p className="mt-3 text-xs leading-relaxed text-slate-300">
                Host your clients’ login portals and call consoles on your own agency domain (e.g., <code className="text-[#24C8D8]">voice.youragency.com</code>) with seamless SSL provisioning.
              </p>
            </div>

            {/* 4. Aggregated Partner Billing (Roadmap) */}
            <div className="rounded-2xl border border-white/10 bg-[#0F1626] p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/30">
                    <Sliders className="h-4 w-4" />
                  </div>
                  <h3 className="text-base font-bold text-white">Pooled Telephony & Usage Visibility</h3>
                </div>
                <span className="rounded bg-[#7657F6]/20 px-2 py-0.5 font-mono text-[10px] font-bold text-[#c4b5fd] border border-[#7657F6]/40">
                  PARTNER ROADMAP
                </span>
              </div>
              <p className="mt-3 text-xs leading-relaxed text-slate-300">
                A unified reseller cockpit to monitor sub-account minute allocations, aggregate call volumes, and manage retainer margins without manual reconciliation.
              </p>
            </div>

            {/* Dedicated Agency CTA */}
            <div className="pt-2">
              <Link
                href="#agency-inquiry"
                className="inline-flex items-center gap-2 rounded-xl bg-[#24C8D8] px-6 py-3.5 text-xs font-bold text-[#070A12] shadow-lg shadow-[#24C8D8]/20 transition hover:bg-[#52e4f2]"
              >
                <span>Apply for Agency Partner Early Access</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>

          {/* Right Column: Illustrative Agency Cockpit Workbench */}
          <div className="lg:col-span-6">
            <div className="rounded-2xl border border-white/15 bg-[#0D1322] p-6 shadow-2xl backdrop-blur-xl">

              {/* Header */}
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-2">
                    <span>Horizon Digital Agency (Partner Cockpit)</span>
                    <span className="rounded bg-[#7657F6]/20 px-2 py-0.5 text-[9px] font-mono text-[#c4b5fd]">
                      Reseller Tier
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Illustrative Sub-Account Fleet: 3 Sample Workspaces
                  </div>
                </div>
                <span className="font-mono text-[9px] uppercase tracking-wider text-slate-500">
                  [ILLUSTRATIVE PREVIEW // DEMO DATA]
                </span>
              </div>

              {/* Sub-account 1 */}
              <div className="mt-5 rounded-xl border border-white/10 bg-[#151D32] p-4 text-xs">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-white">Acme Logistics Group</div>
                    <div className="text-[11px] font-mono text-[#24C8D8]">acme.leadvoix.com</div>
                  </div>
                  <span className="rounded bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-400 border border-emerald-500/30">
                    2 Active Agents
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 border-t border-white/5 pt-2 text-[10px] text-slate-400">
                  <div>Minutes Used: <strong className="text-white">420</strong></div>
                  <div>Leads Created: <strong className="text-white">64</strong></div>
                  <div>Status: <span className="text-emerald-400">Healthy</span></div>
                </div>
              </div>

              {/* Sub-account 2 */}
              <div className="mt-3.5 rounded-xl border border-white/10 bg-[#151D32] p-4 text-xs">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-white">Apex Dental & Orthodontics</div>
                    <div className="text-[11px] font-mono text-[#24C8D8]">apex.leadvoix.com</div>
                  </div>
                  <span className="rounded bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-400 border border-emerald-500/30">
                    1 Active Agent
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 border-t border-white/5 pt-2 text-[10px] text-slate-400">
                  <div>Minutes Used: <strong className="text-white">180</strong></div>
                  <div>Appointments: <strong className="text-white">29</strong></div>
                  <div>Status: <span className="text-emerald-400">Healthy</span></div>
                </div>
              </div>

              {/* Sub-account 3 */}
              <div className="mt-3.5 rounded-xl border border-white/10 bg-[#151D32] p-4 text-xs">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-white">Meridian Family Law</div>
                    <div className="text-[11px] font-mono text-[#24C8D8]">meridian.leadvoix.com</div>
                  </div>
                  <span className="rounded bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-400 border border-emerald-500/30">
                    1 Active Agent
                  </span>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 border-t border-white/5 pt-2 text-[10px] text-slate-400">
                  <div>Minutes Used: <strong className="text-white">290</strong></div>
                  <div>Intakes Logged: <strong className="text-white">41</strong></div>
                  <div>Status: <span className="text-emerald-400">Healthy</span></div>
                </div>
              </div>

              {/* Summary Bottom Bar */}
              <div className="mt-5 rounded-xl border border-white/5 bg-[#080C18] p-3 text-[11px] text-slate-400 flex items-center justify-between">
                <span>Total Client Pooled Minutes:</span>
                <span className="font-mono font-bold text-white">890 / 2,500 Mins</span>
              </div>

            </div>
          </div>

        </div>

      </div>
    </section>
  );
}
