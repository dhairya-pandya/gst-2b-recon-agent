import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Privacy" };

export default function Privacy() {
  return (
    <main className="mx-auto grid w-full max-w-2xl gap-6 px-6 py-24 text-base">
      <h1 className="text-4xl font-semibold tracking-tight">Privacy</h1>
      <p>Milaan is an open source project. This page says what it stores and why.</p>
      <h2 className="text-xl font-semibold">What is stored</h2>
      <p>
        Your email address, for sign in. The clients you add (legal name and GSTIN). For each
        reconciliation: the matched rows, agent notes and your review decisions.
      </p>
      <h2 className="text-xl font-semibold">What is not stored</h2>
      <p>
        Uploaded files. The GSTR-2B, purchase register and invoice PDFs are read in memory during a
        run and then discarded.
      </p>
      <h2 className="text-xl font-semibold">Who can see it</h2>
      <p>
        Only members of your firm. Row level security in the database checks your sign in token on
        every query. For flagged rows, the row details (not your files) are sent to Google&apos;s Gemini
        API to draft an explanation.
      </p>
      <h2 className="text-xl font-semibold">Please do not upload real client data</h2>
      <p>This deployment is a demonstration. Use the synthetic sample files from the home page.</p>
      <Link href="/" className="underline underline-offset-4">Back to Milaan</Link>
    </main>
  );
}
