import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import QueryProvider from "@/providers/QueryProvider";
import ThemeProvider from "@/providers/ThemeProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://www.leadvoix.com"),

  title: "LeadVoix AI | AI Voice Agents, CRM & Call Intelligence",

  description:
    "LeadVoix helps businesses automatically call, qualify and follow up with leads using AI Voice Agents, CRM automation and Call Intelligence.",

  alternates: {
    canonical: "https://www.leadvoix.com/",
  },

  robots: {
    index: true,
    follow: true,
  },

  openGraph: {
    title: "LeadVoix AI | AI Voice Agents, CRM & Call Intelligence",
    description:
      "Automatically call, qualify and follow up with leads using AI Voice Agents, CRM automation and Call Intelligence.",
    url: "https://www.leadvoix.com/",
    siteName: "LeadVoix AI",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable}`}
    >
      <body>
        <QueryProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}