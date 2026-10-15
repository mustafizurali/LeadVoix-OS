
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "AI Voice Agents for Businesses | LeadVoix",
  description:
    "Discover LeadVoix AI Voice Agents for handling business calls, qualifying leads, and connecting conversations with your CRM. Book a demo to explore the platform.",
  alternates: {
    canonical: "https://www.leadvoix.com/ai-voice-agents",
  },
  openGraph: {
    title: "AI Voice Agents for Businesses | LeadVoix",
    description:
      "Handle business calls, qualify leads, and connect customer conversations with your CRM using LeadVoix AI Voice Agents.",
    url: "https://www.leadvoix.com/ai-voice-agents",
    siteName: "LeadVoix",
    type: "website",
  },
};

export default function AIVoiceAgentsPage() {
  return (
    <main className="min-h-screen bg-white text-gray-900">
      <section className="mx-auto max-w-6xl px-6 py-20 md:py-28">
        <p className="mb-4 text-sm font-semibold uppercase tracking-wider text-blue-600">
          LeadVoix AI Voice Agents
        </p>

        <h1 className="max-w-4xl text-4xl font-bold tracking-tight md:text-6xl">
          Turn Business Calls Into Better Customer Opportunities
        </h1>

        <p className="mt-6 max-w-2xl text-lg leading-8 text-gray-600">
          LeadVoix helps businesses manage customer calls, capture lead
         details, identify sales opportunities, and organize follow-ups
         through AI voice agents and CRM-connected workflows. Explore
         how voice automation can support your sales and customer
         communication process. 
        </p>

        <div className="mt-8 flex flex-wrap gap-4">
          <Link
            href="/#contact"
            className="rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700"
          >
            Book a Demo
          </Link>

          <Link
            href="/signup"
            className="rounded-lg border border-gray-300 px-6 py-3 font-semibold hover:bg-gray-50"
          >
            Get Started
          </Link>
        </div>
      </section>

      <section className="border-t border-gray-200 bg-gray-50">
        <div className="mx-auto grid max-w-6xl gap-10 px-6 py-16 md:grid-cols-3">
          <article>
            <h2 className="text-xl font-semibold">
              Manage Business Calls
            </h2>
            <p className="mt-3 leading-7 text-gray-600">
              Support inbound customer conversations and routine call handling
             with AI voice workflows, helping your team manage enquiries more
             consistently.
            </p>
          </article>

          <article>
            <h2 className="text-xl font-semibold">
              Qualify Potential Leads
            </h2>
            <p className="mt-3 leading-7 text-gray-600">
              Capture prospect information, understand customer interest, and
             organize potential leads so your sales team can prioritize
             follow-ups.
            </p>
          </article>

          <article>
            <h2 className="text-xl font-semibold">
              Connect Calls With Your CRM
            </h2>
            <p className="mt-3 leading-7 text-gray-600">
              Connect call information with lead management workflows to keep
              customer conversations, prospect details, and next steps organized
             in one sales process.
            </p>
          </article>
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-6 py-20 text-center">
        <h2 className="text-3xl font-bold">
          Explore LeadVoix for Your Business
        </h2>
        <p className="mt-4 leading-7 text-gray-600">
          See how AI voice agents and CRM workflows could fit into your
          customer communication process.
        </p>
        <Link
          href="/#contact"
          className="mt-7 inline-block rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white hover:bg-blue-700"
        >
          Request a Demo
        </Link>
      </section>
    </main>
  );
}
