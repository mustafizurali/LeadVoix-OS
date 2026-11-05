"use client";

import React from "react";
import { Server, ShieldCheck, Database, Cpu } from "lucide-react";

export default function VerifiedTechStack() {
  const stackItems = [
    {
      title: "Telephony Ingestion",
      tech: "Twilio Voice & Webhooks",
      desc: "Cryptographic HMAC-SHA1 signature validation on every webhook, with proxy header filtering to protect against host-injection.",
      icon: Server,
    },
    {
      title: "Asynchronous Worker Queue",
      tech: "Lease-Fenced Background Engine",
      desc: "Persistent PostgreSQL queue with atomic claim tokens, timestamped heartbeats, and automated dead-letter alerting.",
      icon: Cpu,
    },
    {
      title: "Tenant-Isolated Persistence",
      tech: "PostgreSQL & SQLAlchemy",
      desc: "Relational multi-tenant isolation ensuring each organization's leads, contacts, deals, and audio recordings remain strictly partitioned.",
      icon: Database,
    },
    {
      title: "Deterministic CRM Automation",
      tech: "E.164 Phone Normalization & Workflows",
      desc: "Standardized telephone parsing, contact deduplication, and automatic deal stage state machines that run without human rep delay.",
      icon: ShieldCheck,
    },
  ];

  return (
    <section className="relative z-10 mx-auto max-w-7xl px-5 py-20 lg:px-8">
      <div className="rounded-2xl border border-white/10 bg-[#0A0F1D] p-7 sm:p-10 shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/10 pb-6">
          <div>
            <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#7657F6]">
              ENGINEERING FOUNDATION
            </span>
            <h2 className="mt-2 text-2xl font-black text-white sm:text-4xl">
              Verified Technical Architecture
            </h2>
          </div>
          <p className="max-w-md text-xs leading-relaxed text-slate-400">
            Built on verified telephony standards and relational multi-tenant architecture, not fragile third-party scrapers.
          </p>
        </div>

        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {stackItems.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="rounded-xl border border-white/5 bg-[#12182B] p-5 shadow-sm"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 text-[#24C8D8]">
                  <Icon className="h-4 w-4" />
                </div>
                <h3 className="mt-4 font-bold text-sm text-white">{item.title}</h3>
                <div className="mt-1 font-mono text-[10px] text-[#7657F6] font-semibold">
                  {item.tech}
                </div>
                <p className="mt-2 text-xs leading-relaxed text-slate-400">
                  {item.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
