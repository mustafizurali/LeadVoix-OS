"use client";

import React from "react";
import Link from "next/link";

interface LeadVoixLogoProps {
  size?: "sm" | "md" | "lg";
  variant?: "full" | "mark" | "stacked";
  href?: string;
  className?: string;
  glow?: boolean;
}

export function VoiceWaveMark({
  size = "md",
  glow = false,
  className = "",
}: {
  size?: "sm" | "md" | "lg";
  glow?: boolean;
  className?: string;
}) {
  const dimensions = {
    sm: { box: "h-7 w-7", svg: 28 },
    md: { box: "h-9 w-9", svg: 36 },
    lg: { box: "h-11 w-11", svg: 44 },
  }[size];

  return (
    <div
      className={`relative inline-flex shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[#1A233D] via-[#121A2F] to-[#0B1020] p-1.5 shadow-md shadow-violet-950/40 border border-white/10 ${dimensions.box} ${className}`}
    >
      {/* Ambient background glow */}
      {glow && (
        <div className="pointer-events-none absolute -inset-1 rounded-xl bg-gradient-to-r from-[#7657F6]/40 to-[#24C8D8]/40 opacity-70 blur-md transition-opacity group-hover:opacity-100" />
      )}

      <svg
        viewBox="0 0 36 36"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="relative h-full w-full"
        aria-hidden="true"
      >
        <defs>
          <linearGradient
            id="lv-voice-wave-gradient"
            x1="4"
            y1="6"
            x2="32"
            y2="30"
            gradientUnits="userSpaceOnUse"
          >
            <stop offset="0%" stopColor="#7657F6" />
            <stop offset="50%" stopColor="#9B7DFE" />
            <stop offset="100%" stopColor="#24C8D8" />
          </linearGradient>

          <linearGradient
            id="lv-pulse-center"
            x1="16"
            y1="15"
            x2="20"
            y2="31"
            gradientUnits="userSpaceOnUse"
          >
            <stop offset="0%" stopColor="#24C8D8" />
            <stop offset="100%" stopColor="#35D6C1" />
          </linearGradient>
        </defs>

        {/* Outer Left Bar */}
        <rect
          x="4.5"
          y="6.5"
          width="3.5"
          height="18"
          rx="1.75"
          fill="url(#lv-voice-wave-gradient)"
        />

        {/* Mid-Left Bar */}
        <rect
          x="10.5"
          y="11.5"
          width="3.5"
          height="16"
          rx="1.75"
          fill="url(#lv-voice-wave-gradient)"
        />

        {/* Center Apex V-Bar (focal soundwave) */}
        <rect
          x="16.25"
          y="16.5"
          width="3.5"
          height="14"
          rx="1.75"
          fill="url(#lv-pulse-center)"
        />

        {/* Mid-Right Bar */}
        <rect
          x="22"
          y="11.5"
          width="3.5"
          height="16"
          rx="1.75"
          fill="url(#lv-voice-wave-gradient)"
        />

        {/* Outer Right Bar */}
        <rect
          x="28"
          y="6.5"
          width="3.5"
          height="18"
          rx="1.75"
          fill="url(#lv-voice-wave-gradient)"
        />
      </svg>
    </div>
  );
}

export default function LeadVoixLogo({
  size = "md",
  variant = "full",
  href = "/",
  className = "",
  glow = true,
}: LeadVoixLogoProps) {
  const textSizes = {
    sm: "text-base tracking-tight",
    md: "text-lg tracking-tight",
    lg: "text-2xl tracking-tight",
  }[size];

  const badgeSizes = {
    sm: "text-[9px] px-1.5 py-0.2",
    md: "text-[10px] px-1.5 py-0.5",
    lg: "text-xs px-2 py-0.5",
  }[size];

  const content = (
    <div
      className={`group inline-flex items-center gap-2.5 select-none transition-opacity hover:opacity-95 ${className}`}
    >
      <VoiceWaveMark size={size} glow={glow} />

      {variant !== "mark" && (
        <div className="flex items-center gap-1.5">
          <span
            className={`font-black font-sans text-[#F5F7FC] ${textSizes}`}
          >
            Lead<span className="text-[#F5F7FC]">Voix</span>
          </span>
          <span
            className={`rounded-md border border-[#24C8D8]/30 bg-[#24C8D8]/10 font-mono font-bold text-[#24C8D8] tracking-wider uppercase ${badgeSizes}`}
          >
            OS
          </span>
        </div>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href} aria-label="LeadVoix OS - Home">
        {content}
      </Link>
    );
  }

  return content;
}
