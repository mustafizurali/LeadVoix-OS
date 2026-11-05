"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

export default function EnterpriseFaq() {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const toggleFaq = (idx: number) => {
    setOpenFaq(openFaq === idx ? null : idx);
  };

  const faqs = [
    {
      q: "How does the 7-Day Free Trial work?",
      a: "The free trial includes up to 30 calling minutes and 7 days of platform access to explore autonomous agent creation and CRM pipeline automation. No credit card is required to sign up, with zero automatic renewal or billing obligations. Please note that automated backend quota enforcement is currently in active development on our platform roadmap.",
    },
    {
      q: "Can we use our existing company phone numbers?",
      a: "Yes. You can either provision dedicated local or toll-free numbers directly through LeadVoix or forward calls from your existing carrier lines (AT&T, Verizon, RingCentral, etc.) directly to your designated LeadVoix telephony endpoints.",
    },
    {
      q: "Does LeadVoix create CRM records automatically?",
      a: "Yes. Following each call, our background worker normalizes the phone number into international E.164 format, matches existing Contacts, creates or updates Lead records, posts structured intelligence summaries, dispatches follow-up Tasks with due dates, and advances your CRM Deal stages without manual rep intervention.",
    },
    {
      q: "How does the Agency & White Label Partner Program work?",
      a: "The partner program enables digital marketing agencies, MSPs, and voice consultants to manage multiple client organizations. In the current platform, each client receives a dedicated, tenant-isolated organization workspace. Custom domain CNAME mapping, white-label client branding, and pooled partner billing are currently in active pilot evaluation on our partner roadmap.",
    },
    {
      q: "What happens if a caller asks complex or off-script questions?",
      a: "LeadVoix agents operate with strict knowledge base guardrails. If a caller requests a human representative or asks questions outside the agent's authorized scope, the agent politely initiates a live transfer procedure to your designated sales desk or logs a high-priority callback task.",
    },
    {
      q: "How does additional per-minute billing work?",
      a: "Each plan comes with a generous monthly minute allocation (300, 1,000, or 2,500 minutes). Any usage beyond your monthly plan is billed at a flat rate of $0.25 per minute with zero surprise surcharges or variable fees.",
    },
  ];

  return (
    <section id="faq" className="relative z-10 mx-auto max-w-4xl px-5 py-20 lg:px-8 lg:py-28">
      <div className="text-center">
        <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#7657F6]">
          FREQUENTLY ASKED QUESTIONS
        </span>
        <h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-4xl">
          Everything You Need to Know
        </h2>
      </div>

      <div className="mt-12 space-y-4">
        {faqs.map((item, idx) => (
          <div
            key={idx}
            className="rounded-xl border border-white/10 bg-[#0E1424] overflow-hidden"
          >
            <button
              type="button"
              onClick={() => toggleFaq(idx)}
              className="flex w-full items-center justify-between p-5 text-left text-sm font-bold text-white transition hover:text-[#24C8D8]"
            >
              <span>{item.q}</span>
              {openFaq === idx ? (
                <ChevronUp className="h-4 w-4 text-[#24C8D8] shrink-0 ml-4" />
              ) : (
                <ChevronDown className="h-4 w-4 text-slate-400 shrink-0 ml-4" />
              )}
            </button>
            {openFaq === idx && (
              <div className="border-t border-white/5 px-5 pb-5 pt-3 text-xs leading-relaxed text-slate-300">
                {item.a}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
