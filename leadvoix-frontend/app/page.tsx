import React from "react";
import EditorialNav from "@/components/landing/EditorialNav";
import HeroEnterprise from "@/components/landing/HeroEnterprise";
import VoiceAgentPersonas from "@/components/landing/VoiceAgentPersonas";
import InteractiveWorkflowEngine from "@/components/landing/InteractiveWorkflowEngine";
import ProductShowcaseWorkbench from "@/components/landing/ProductShowcaseWorkbench";
import VoiceIntelligenceTimeline from "@/components/landing/VoiceIntelligenceTimeline";
import AgencyWhiteLabelSection from "@/components/landing/AgencyWhiteLabelSection";
import EnterpriseUseCases from "@/components/landing/EnterpriseUseCases";
import VerifiedTechStack from "@/components/landing/VerifiedTechStack";
import EnterprisePricing from "@/components/landing/EnterprisePricing";
import EnterpriseFaq from "@/components/landing/EnterpriseFaq";
import DemoAndPartnerBooking from "@/components/landing/DemoAndPartnerBooking";
import EnterpriseFooter from "@/components/landing/EnterpriseFooter";

export const metadata = {
  title: "LeadVoix OS — Enterprise AI Voice, CRM & Revenue Automation",
  description:
    "Deploy autonomous AI voice agents that handle multi-turn customer calls, extract commercial intent, and commit structured Leads, follow-up Tasks, and Deals directly into your CRM.",
};

export default function HomePage() {
  return (
    <main className="min-h-screen overflow-x-hidden bg-[#070A12] text-[#F5F7FC] selection:bg-[#7657F6]/30 font-sans">
      {/* Subtle architectural ambient lighting */}
      <div className="pointer-events-none fixed inset-0 -z-0">
        <div className="absolute left-1/2 top-[-250px] h-[600px] w-[950px] -translate-x-1/2 rounded-full bg-[#7657F6]/10 blur-[160px]" />
        <div className="absolute right-[-150px] top-[450px] h-[500px] w-[500px] rounded-full bg-[#24C8D8]/5 blur-[150px]" />
        <div className="absolute left-[-150px] top-[1400px] h-[600px] w-[600px] rounded-full bg-[#7657F6]/5 blur-[170px]" />
        <div className="absolute right-[-100px] bottom-[400px] h-[550px] w-[550px] rounded-full bg-[#24C8D8]/5 blur-[150px]" />
      </div>

      {/* 1. Slim Editorial Header & Navigation */}
      <EditorialNav />

      {/* 2. Asymmetrical Hero with 7-Day Free Trial & Genuine Dashboard Showcase */}
      <HeroEnterprise />

      {/* 3. AI Voice Agent Personas (Receptionist, Sales SDR, After-Hours Support) */}
      <VoiceAgentPersonas />

      {/* 4. Interactive Call-to-Cash Workflow Engine with Genuine Product Screenshots */}
      <InteractiveWorkflowEngine />

      {/* 5. Product Showcase Workbench (Voice + CRM in Tandem) */}
      <ProductShowcaseWorkbench />

      {/* 6. Voice Intelligence Timeline (Execution Model: Streaming vs Async Worker) */}
      <VoiceIntelligenceTimeline />

      {/* 7. Dedicated Agency & White Label Partner Section */}
      <AgencyWhiteLabelSection />

      {/* 8. Industry Scenarios (High-Volume Enterprise Use Cases) */}
      <EnterpriseUseCases />

      {/* 9. Verified Technical Stack Schematic */}
      <VerifiedTechStack />

      {/* 10. Transparent Pricing with 7-Day Free Trial & Preserved Prices */}
      <EnterprisePricing />

      {/* 11. Frequently Asked Questions */}
      <EnterpriseFaq />

      {/* 13. High-Conversion Demo & Partner Application */}
      <DemoAndPartnerBooking />

      {/* 14. Professional Editorial Corporate Footer */}
      <EnterpriseFooter />
    </main>
  );
}
