import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Terms" };

export default function Terms() {
  return (
    <main className="mx-auto grid w-full max-w-2xl gap-6 px-6 py-24 text-base">
      <h1 className="text-4xl font-semibold tracking-tight">Terms</h1>
      <p>
        Milaan is a free, open source demonstration. It is provided as is, without any warranty, and
        is not tax advice.
      </p>
      <p>
        Verdicts and agent notes help you find mismatches. Whether input tax credit can be claimed is
        a professional judgement that stays with you and your firm.
      </p>
      <p>Do not upload real client data to this deployment. Use the synthetic sample files instead.</p>
      <p>Access may be rate limited or withdrawn at any time.</p>
      <Link href="/" className="underline underline-offset-4">Back to Milaan</Link>
    </main>
  );
}
