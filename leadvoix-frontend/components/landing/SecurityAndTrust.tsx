"use client";

import React from "react";
import { ShieldCheck, Lock, Server, Cpu } from "lucide-react";

export default function SecurityAndTrust() {
  const securityPillars = [
    {
      title: "Organization Multi-Tenant Boundary",
      desc: "All contacts, calls, recordings, intelligence, and deals are partitioned at the organization boundary in PostgreSQL via tenant-isolated queries.",
      icon: ShieldCheck,
      color: "#24C8D8",
    },
    {
      title: "Twilio HMAC-SHA1 Validation",
      desc: "Strict request signature validation on every inbound webhook, combined with reverse-proxy host header filtering to eliminate host-injection risks.",
      icon: Lock,
      color: "#7657F6",
    },
    {
      title: "Lease-Fenced Worker Persistence",
      desc: "Background jobs utilize atomic claim tokens and heartbeats in PostgreSQL to prevent race conditions and minimize duplicate task execution.",
      icon: Cpu,
      color: "#24C8D8",
    },
    {
      title: "Dead-Letter Queue & Recovery",
      desc: "Failed post-call analyses automatically trigger dead-letter alerting and exponential retry backoff for resilient call processing.",
      icon: Server,
      color: "#7657F6",
    },
  ];

  return (
    <section id="security" className="relative z-10 border-y border-white/10 bg-[#080D1A] py-20 lg:py-28">
      <div className="mx-auto max-w-7xl px-5 lg:px-8">
        <div className="max-w-3xl">
          <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#24C8D8]">
            DATA GOVERNANCE & ARCHITECTURE
          </span>
          <h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-5xl">
            Enterprise Security Verified by Code
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-slate-300">
            We do not rely on vague marketing badges. Every safeguard below is an active, verified component of our production codebase.
          </p>
        </div>

        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {securityPillars.map((pillar, idx) => {
            const Icon = pillar.icon;
            return (
              <div
                key={idx}
                className="rounded-2xl border border-white/10 bg-[#0E1424] p-6 shadow-md"
              >
                <div
                  style={{ color: pillar.color, backgroundColor: `${pillar.color}15`, borderColor: `${pillar.color}30` }}
                  className="flex h-10 w-10 items-center justify-center rounded-xl border"
                >
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 text-base font-bold text-white">{pillar.title}</h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-400">
                  {pillar.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
