"use client";

import React, { useState, useEffect } from "react";
import { ArrowRight, CheckCircle2, Building, Bot, Mail, Phone, User, MessageSquare } from "lucide-react";

export default function DemoAndPartnerBooking() {
  const [inquiryType, setInquiryType] = useState<"demo" | "agency">("demo");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const checkHash = () => {
      if (
        window.location.hash === "#agency-inquiry" ||
        window.location.hash === "#partner"
      ) {
        setInquiryType("agency");
      }
    };
    checkHash();
    window.addEventListener("hashchange", checkHash);
    return () => window.removeEventListener("hashchange", checkHash);
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    setSuccess("");

    const form = e.currentTarget;
    const formData = new FormData(form);

    const payload = {
      name: formData.get("name") as string,
      email: formData.get("email") as string,
      company: formData.get("company") as string,
      phone: (formData.get("phone") as string) || undefined,
      message: `${inquiryType === "agency" ? "[AGENCY / WHITE-LABEL INQUIRY] " : ""}${
        (formData.get("message") as string) || ""
      }`.trim(),
    };

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/demo-requests/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Failed to submit request.");
      }

      setSuccess(
        inquiryType === "agency"
          ? "Thank you! Our agency partner solutions team will reach out with early access documentation."
          : "Thank you! Our enterprise engineering team will contact you shortly to schedule your demo."
      );
      form.reset();
    } catch (err) {
      console.error("Booking submission error:", err);
      setError("Unable to submit request at this moment. Please try again or reach out directly.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section id="contact" className="relative z-10 mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
      <div id="agency-inquiry" className="absolute -top-12" />
      <div className="overflow-hidden rounded-3xl border border-[#7657F6]/30 bg-gradient-to-br from-[#12192E] via-[#0E1528] to-[#080D1A] p-7 sm:p-12 shadow-2xl">
        <div className="grid gap-12 lg:grid-cols-12 lg:items-center">

          {/* Left Column: Briefing & Value Prop */}
          <div className="lg:col-span-5">
            <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[#24C8D8]">
              LIVE DEMO & PARTNER INQUIRY
            </span>
            <h2 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-4xl">
              Schedule a Live Demo
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-slate-300">
              Schedule a live demonstration with our team or apply for the Agency & White Label Partner Program.
            </p>

            <div className="mt-8 space-y-4 text-xs text-slate-300">
              <div className="flex items-start gap-3">
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#7657F6]/20 text-[#24C8D8]">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                </div>
                <span>Live conversational simulation with your industry knowledge base</span>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#7657F6]/20 text-[#24C8D8]">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                </div>
                <span>Full CRM pipeline stage mutation and task assignment walkthrough</span>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#7657F6]/20 text-[#24C8D8]">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                </div>
                <span>Dedicated telephony number provisioning & carrier call-forwarding review</span>
              </div>
              <div className="flex items-start gap-3">
                <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#24C8D8]/20 text-[#24C8D8]">
                  <Building className="h-3.5 w-3.5" />
                </div>
                <span>Agency multi-client architecture & early-access roadmap briefing</span>
              </div>
            </div>
          </div>

          {/* Right Column: Tabbed Form */}
          <div className="lg:col-span-7">
            <div className="rounded-2xl border border-white/10 bg-[#0A0F1D] p-6 sm:p-8 shadow-xl">

              {/* Type Switcher Tabs */}
              <div className="flex rounded-xl border border-white/10 bg-[#060A14] p-1 text-xs mb-6">
                <button
                  type="button"
                  onClick={() => setInquiryType("demo")}
                  className={`flex-1 flex items-center justify-center gap-2 rounded-lg py-2.5 font-bold transition ${
                    inquiryType === "demo"
                      ? "bg-[#7657F6] text-white shadow-sm"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  <Bot className="h-3.5 w-3.5" />
                  <span>Direct Enterprise Demo</span>
                </button>
                <button
                  type="button"
                  onClick={() => setInquiryType("agency")}
                  className={`flex-1 flex items-center justify-center gap-2 rounded-lg py-2.5 font-bold transition ${
                    inquiryType === "agency"
                      ? "bg-[#24C8D8] text-[#070A12] shadow-sm"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  <Building className="h-3.5 w-3.5" />
                  <span>Agency & White Label Partner</span>
                </button>
              </div>

              {/* Status Notifications */}
              {success && (
                <div className="mb-6 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-xs font-medium text-emerald-400">
                  {success}
                </div>
              )}
              {error && (
                <div className="mb-6 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-xs font-medium text-rose-400">
                  {error}
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-4 text-xs">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="block font-semibold text-slate-300 mb-1.5">
                      Your Full Name *
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <input
                        type="text"
                        name="name"
                        required
                        placeholder="Marcus Vance"
                        className="w-full rounded-xl border border-white/10 bg-[#12182B] py-2.5 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:border-[#7657F6] focus:outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-300 mb-1.5">
                      Work Email *
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <input
                        type="email"
                        name="email"
                        required
                        placeholder="marcus@vancelogistics.com"
                        className="w-full rounded-xl border border-white/10 bg-[#12182B] py-2.5 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:border-[#7657F6] focus:outline-none"
                      />
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="block font-semibold text-slate-300 mb-1.5">
                      Company / Agency Name *
                    </label>
                    <div className="relative">
                      <Building className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <input
                        type="text"
                        name="company"
                        required
                        placeholder="Vance Logistics"
                        className="w-full rounded-xl border border-white/10 bg-[#12182B] py-2.5 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:border-[#7657F6] focus:outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block font-semibold text-slate-300 mb-1.5">
                      Direct Phone Number
                    </label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                      <input
                        type="tel"
                        name="phone"
                        placeholder="+1 (415) 890-2341"
                        className="w-full rounded-xl border border-white/10 bg-[#12182B] py-2.5 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:border-[#7657F6] focus:outline-none"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block font-semibold text-slate-300 mb-1.5">
                    {inquiryType === "agency"
                      ? "Estimated Client Accounts & Special Requirements"
                      : "Primary Business Requirements & Current CRM"}
                  </label>
                  <div className="relative">
                    <MessageSquare className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
                    <textarea
                      name="message"
                      rows={3}
                      placeholder={
                        inquiryType === "agency"
                          ? "We manage 12 dental practices looking for after-hours appointment booking..."
                          : "We receive ~800 inbound calls/month and want to automate Lead creation..."
                      }
                      className="w-full rounded-xl border border-white/10 bg-[#12182B] py-2.5 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:border-[#7657F6] focus:outline-none"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className={`w-full rounded-xl py-3.5 text-xs font-bold transition shadow-lg flex items-center justify-center gap-2 ${
                    inquiryType === "agency"
                      ? "bg-[#24C8D8] text-[#070A12] hover:bg-[#52e4f2]"
                      : "bg-[#7657F6] text-white hover:bg-[#6846ed]"
                  }`}
                >
                  {submitting ? (
                    <span>Submitting Inquiry...</span>
                  ) : inquiryType === "agency" ? (
                    <>
                      <span>Submit Agency Partner Application</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  ) : (
                    <>
                      <span>Schedule a Live Demo</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
