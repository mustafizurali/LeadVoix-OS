"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, Menu, X, Sparkles } from "lucide-react";
import LeadVoixLogo from "@/components/brand/LeadVoixLogo";

export default function EditorialNav() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.08] bg-[#070A12]/90 backdrop-blur-xl transition-all">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <LeadVoixLogo size="md" href="/" />
        </div>

        {/* Desktop Navigation Links */}
        <nav className="hidden items-center gap-7 lg:flex">
          <Link
            href="#personas"
            className="text-xs font-semibold uppercase tracking-wider text-slate-300 transition hover:text-white"
          >
            Voice Personas
          </Link>
          <Link
            href="#workflow"
            className="text-xs font-semibold uppercase tracking-wider text-slate-300 transition hover:text-white"
          >
            Workflow
          </Link>
          <Link
            href="#product"
            className="text-xs font-semibold uppercase tracking-wider text-slate-300 transition hover:text-white"
          >
            CRM Platform
          </Link>
          <Link
            href="#agency"
            className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[#24C8D8] transition hover:text-[#52e4f2]"
          >
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#24C8D8] animate-pulse" />
            Agency & Resellers
          </Link>
          <Link
            href="#pricing"
            className="text-xs font-semibold uppercase tracking-wider text-slate-300 transition hover:text-white"
          >
            Pricing
          </Link>
        </nav>

        {/* Free Trial Pill & Action Buttons */}
        <div className="hidden items-center gap-3.5 md:flex">
          <div className="hidden xl:flex items-center gap-1.5 rounded-full border border-[#7657F6]/30 bg-[#7657F6]/10 px-2.5 py-1 text-[11px] font-medium text-[#c4b5fd]">
            <Sparkles className="h-3 w-3 text-[#24C8D8]" />
            <span>7-Day Free Trial (30 Mins)</span>
          </div>

          <Link
            href="/login"
            className="text-xs font-semibold text-slate-300 transition hover:text-white px-2 py-1.5"
          >
            Sign In
          </Link>

          <Link
            href="/signup"
            className="group inline-flex items-center gap-1.5 rounded-lg bg-[#7657F6] px-3.5 py-2 text-xs font-bold text-white shadow-lg shadow-[#7657F6]/25 transition hover:bg-[#6846ed]"
          >
            <span>Start Free Trial</span>
            <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>

        {/* Mobile Hamburger Button */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 text-slate-300 lg:hidden"
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="border-b border-white/10 bg-[#070A12]/98 px-5 py-6 lg:hidden">
          <nav className="flex flex-col space-y-4">
            <Link
              href="#personas"
              onClick={() => setMobileMenuOpen(false)}
              className="text-sm font-semibold text-slate-200"
            >
              Voice Personas
            </Link>
            <Link
              href="#workflow"
              onClick={() => setMobileMenuOpen(false)}
              className="text-sm font-semibold text-slate-200"
            >
              Workflow
            </Link>
            <Link
              href="#product"
              onClick={() => setMobileMenuOpen(false)}
              className="text-sm font-semibold text-slate-200"
            >
              CRM Platform
            </Link>
            <Link
              href="#agency"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-2 text-sm font-semibold text-[#24C8D8]"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-[#24C8D8]" />
              Agency & Resellers
            </Link>
            <Link
              href="#pricing"
              onClick={() => setMobileMenuOpen(false)}
              className="text-sm font-semibold text-slate-200"
            >
              Pricing
            </Link>

            <div className="pt-4 border-t border-white/10 space-y-3">
              <div className="flex items-center gap-1.5 text-xs text-[#c4b5fd]">
                <Sparkles className="h-3.5 w-3.5 text-[#24C8D8]" />
                <span>7-Day Free Trial • 30 Mins • No Card Required</span>
              </div>
              <Link
                href="/login"
                className="block text-center rounded-lg border border-white/10 bg-white/5 py-2.5 text-xs font-semibold text-white"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="block text-center rounded-lg bg-[#7657F6] py-2.5 text-xs font-bold text-white shadow-md"
              >
                Start 7-Day Free Trial
              </Link>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
