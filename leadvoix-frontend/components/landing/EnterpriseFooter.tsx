"use client";

import React from "react";
import Link from "next/link";
import LeadVoixLogo from "@/components/brand/LeadVoixLogo";

export default function EnterpriseFooter() {
  return (
    <footer className="relative z-10 border-t border-white/10 bg-[#060A14] py-16">
      <div className="mx-auto max-w-7xl px-5 lg:px-8">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-5">
          {/* Brand Info */}
          <div className="lg:col-span-2 space-y-4">
            <LeadVoixLogo size="md" href="/" />
            <p className="max-w-sm text-xs leading-relaxed text-slate-400">
              Autonomous AI Voice Agents connected directly to relational CRM pipelines, multi-tenant organization boundaries, and automatic follow-up tasks.
            </p>
            <div className="flex items-center gap-2 pt-2 text-xs text-slate-500 font-mono">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <span>Production Telephony Engine Active</span>
            </div>
          </div>

          {/* Column 1: Direct Platform */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-white font-mono">
              Direct Platform
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>
                <Link href="/dashboard" className="hover:text-white transition">
                  Dashboard
                </Link>
              </li>
              <li>
                <Link href="/agent-calls" className="hover:text-white transition">
                  Agent Call Logs
                </Link>
              </li>
              <li>
                <Link href="/leads" className="hover:text-white transition">
                  CRM Leads
                </Link>
              </li>
              <li>
                <Link href="/deals" className="hover:text-white transition">
                  Deals & Pipelines
                </Link>
              </li>
              <li>
                <Link href="/tasks" className="hover:text-white transition">
                  Follow-up Tasks
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 2: Agency & Resellers */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#24C8D8] font-mono">
              Agency & Partners
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>
                <Link href="#agency" className="hover:text-[#24C8D8] transition">
                  White Label Overview
                </Link>
              </li>
              <li>
                <Link href="#agency" className="hover:text-[#24C8D8] transition">
                  Multi-Client Hierarchy
                </Link>
              </li>
              <li>
                <Link href="#pricing" className="hover:text-[#24C8D8] transition">
                  Reseller Fleet Pricing
                </Link>
              </li>
              <li>
                <Link href="#agency-inquiry" className="hover:text-[#24C8D8] transition">
                  Partner Application
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Legal & Governance */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-white font-mono">
              Legal & Trust
            </h4>
            <ul className="space-y-2 text-xs text-slate-400">
              <li>
                <Link href="/terms" className="hover:text-white transition">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="hover:text-white transition">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/refund" className="hover:text-white transition">
                  Refund Policy
                </Link>
              </li>
              <li>
                <Link href="/voice-disclosure" className="hover:text-white transition">
                  AI Voice Disclosure
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            &copy; {new Date().getFullYear()} LeadVoix AI Inc. All rights reserved.
          </div>
          <div className="flex items-center gap-6">
            <Link href="/login" className="hover:text-slate-400 transition">
              Sign In
            </Link>
            <Link href="/signup" className="hover:text-slate-400 transition">
              Start Free Trial
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
