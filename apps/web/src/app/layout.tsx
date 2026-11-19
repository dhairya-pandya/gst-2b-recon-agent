import type { Metadata } from "next";
import { Suspense, type ReactNode } from "react";
import { Geist_Mono, Manrope } from "next/font/google";
import { AppShell } from "@/components/app-shell";
import "./globals.css";

const manrope = Manrope({ variable: "--font-manrope", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

const description =
  "Milaan matches a client's GSTR-2B to the purchase register and invoice PDFs, explains every mismatch, and keeps a reviewed record before input tax credit is claimed.";

export const metadata: Metadata = {
  title: { default: "Milaan, GSTR-2B reconciliation for CA firms", template: "%s | Milaan" },
  description,
  applicationName: "Milaan",
  openGraph: {
    title: "Milaan, GSTR-2B reconciliation for CA firms",
    description,
    type: "website",
  },
  twitter: { card: "summary_large_image", title: "Milaan", description },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en-IN" className={`${manrope.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-ink focus:px-3 focus:py-2 focus:text-paper"
        >
          Skip to content
        </a>
        <Suspense fallback={null}>
          <AppShell>{children}</AppShell>
        </Suspense>
      </body>
    </html>
  );
}
