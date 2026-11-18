import type { Metadata } from "next";
import { Suspense, type ReactNode } from "react";
import { Commissioner } from "next/font/google";
import { AppShell } from "@/components/app-shell";
import "./globals.css";

const commissioner = Commissioner({
  variable: "--font-commissioner",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GST 2B Recon",
  description: "Reconcile GSTR-2B against the purchase register.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${commissioner.variable} h-full antialiased`}>
      <body className="min-h-full">
        <Suspense fallback={null}>
          <AppShell>{children}</AppShell>
        </Suspense>
      </body>
    </html>
  );
}
