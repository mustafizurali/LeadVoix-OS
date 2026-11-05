import React, { Suspense } from "react";
import Link from "next/link";
import LoginForm from "@/modules/auth/components/LoginForm";
import LeadVoixLogo from "@/components/brand/LeadVoixLogo";

export default function LoginPage() {
  return (
    <main className="relative min-h-screen flex flex-col justify-between bg-[#0B1020] text-[#F5F7FC] selection:bg-[#7657F6]/30 px-4 py-6 sm:px-6 sm:py-8 overflow-x-hidden font-sans">
      {/* Ambient background glow accents */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-15%,rgba(118,87,246,0.18),rgba(11,16,32,0))]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-80 w-80 rounded-full bg-[#24C8D8]/5 blur-3xl" />

      {/* Header */}
      <header className="relative z-10 mx-auto flex w-full max-w-5xl items-center justify-between pb-6">
        <LeadVoixLogo size="md" href="/" />

        <Link
          href="/signup"
          className="text-xs sm:text-sm font-medium text-[#AAB4CC] transition-colors hover:text-[#24C8D8]"
        >
          Don&apos;t have an account?{" "}
          <span className="font-semibold text-[#24C8D8] underline-offset-4 hover:underline">
            Sign up
          </span>
        </Link>
      </header>

      {/* Main Form Center */}
      <div className="relative z-10 flex flex-1 items-center justify-center py-4">
        <Suspense
          fallback={
            <div className="h-96 w-full max-w-md animate-pulse rounded-2xl border border-slate-800/80 bg-[#151D32]/80" />
          }
        >
          <LoginForm />
        </Suspense>
      </div>

      {/* Footer */}
      <footer className="relative z-10 mx-auto w-full max-w-5xl pt-6 text-center text-xs text-[#AAB4CC]/50">
        &copy; {new Date().getFullYear()} LeadVoix AI Inc. All rights reserved.
      </footer>
    </main>
  );
}
