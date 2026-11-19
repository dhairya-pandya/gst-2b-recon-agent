import Link from "next/link";
import {
  ArrowsLeftRight,
  ChatText,
  CheckSquareOffset,
  FileArrowUp,
  ListChecks,
  ShieldCheck,
  Stamp,
  UserPlus,
} from "@phosphor-icons/react/dist/ssr";
import { HeroLedger } from "@/components/landing/hero-ledger";
import { Reveal } from "@/components/landing/reveal";
import { TaglineReveal } from "@/components/landing/tagline-reveal";
import { VerdictStamp, type Verdict } from "@/components/verdict-stamp";
import { ui } from "@/lib/ui";

const CTA = "Start a free reconciliation";

const PROOF = [
  { value: "370 ms", label: "to match 20,000 invoices in the published benchmark" },
  { value: "54,099", label: "invoices matched per second on one laptop, in the same benchmark" },
  { value: "₹1", label: "tolerance per tax head, so paise rounding never raises a flag" },
];

const BENEFITS = [
  {
    icon: Stamp,
    title: "Every invoice gets a verdict",
    body: "Matched, Check, Missing or Duplicate, decided by fixed rules you can read. A language model never sets a verdict.",
  },
  {
    icon: ArrowsLeftRight,
    title: "Near misses still match",
    body: "INV/0042 and inv 42 are the same invoice. Supplier branches under one PAN are recognised instead of flagged as missing.",
  },
  {
    icon: ChatText,
    title: "Mismatches come with a reason",
    body: "Gemini writes the likely cause and next step for each flagged row. A checker warns when a note quotes a figure the source rows do not contain.",
  },
  {
    icon: ListChecks,
    title: "A record of every decision",
    body: "Accept or reject each flagged row. Decisions are saved with the run, so the file shows who cleared what.",
  },
  {
    icon: ShieldCheck,
    title: "Each firm sees only its own clients",
    body: "Row level security in Postgres scopes every query to your firm, using your own sign in token.",
  },
];

const STEPS = [
  { icon: UserPlus, title: "Add the client", body: "Legal name and the 15 character GSTIN from the registration certificate." },
  { icon: FileArrowUp, title: "Upload the month", body: "The GSTR-2B JSON from the portal, the purchase register as CSV, and invoice PDFs if you have them." },
  { icon: CheckSquareOffset, title: "Clear the flagged rows", body: "Read the reason on each flagged invoice, then accept or reject it. Matched rows need nothing." },
];

const VERDICTS: { verdict: Verdict; meaning: string }[] = [
  { verdict: "matched", meaning: "Invoice number, date and every tax amount agree to within ₹1." },
  { verdict: "partial", meaning: "Amounts differ, the PDF total disagrees, or the supplier files under another branch. Review before claiming credit." },
  { verdict: "missing_in_2b", meaning: "The invoice is in one source only: the GSTR-2B or the purchase register." },
  { verdict: "duplicate", meaning: "The same invoice appears more than once in the purchase register." },
];

const FAQ = [
  {
    q: "Which files do I need?",
    a: "The GSTR-2B JSON downloaded from the GST portal and the purchase register as a CSV. Invoice PDFs are optional; when you add them, Milaan checks each PDF total against the matching book entry.",
  },
  {
    q: "Can I try it without real client data?",
    a: "Yes. Download the synthetic sample files below, add any test client, and run them. One invoice PDF is deliberately ₹70.00 off so you can see a flagged row.",
  },
  {
    q: "Does the AI decide whether credit is allowed?",
    a: "No. Verdicts come from deterministic matching rules. The model only explains flagged rows, and its notes never change a verdict.",
  },
  {
    q: "What happens to the files I upload?",
    a: "They are read in memory and not kept. Only the resulting rows, agent notes and your review decisions are stored with the run.",
  },
  {
    q: "How large a return can one run handle?",
    a: "Up to 50,000 rows across both files, 200 invoice PDFs, and 10 MB per file.",
  },
  {
    q: "What about scanned invoice PDFs?",
    a: "PDFs without a text layer are marked as needing OCR instead of being guessed at. Their book rows are still matched against the GSTR-2B.",
  },
  {
    q: "Can an agent note be wrong?",
    a: "Yes, which is why a checker compares every figure in a note with the source rows and warns you when they disagree. Treat notes as a first read, not a ruling.",
  },
  {
    q: "What does it cost?",
    a: "Nothing. Milaan is an open source project, free to use, with no card and no trial clock.",
  },
];

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-6xl px-6 md:px-8">
      {/* Hero */}
      <section className="grid items-center gap-12 pb-24 pt-16 md:pt-24 lg:grid-cols-[1fr_1.05fr]">
        <div className="grid gap-6">
          <h1 className="max-w-[680px] bg-gradient-to-r from-black to-[#666666] bg-clip-text text-4xl font-bold tracking-tight text-transparent sm:text-5xl xl:text-6xl">
            Match every <span className="whitespace-nowrap">GSTR‑2B</span> invoice
            <br className="hidden sm:block" /> to the books before
            <br className="hidden sm:block" /> you claim credit
          </h1>
          <p className="max-w-[680px] text-lg text-ink-soft">
            Milaan reads a client&apos;s GSTR-2B, purchase register and invoice PDFs, gives every
            invoice a verdict, and explains each mismatch in plain words. Your team reviews only the
            rows that need judgement.
          </p>
          <div className="flex flex-wrap items-center gap-4">
            <Link href="/sign-in" className={ui.primary}>
              {CTA}
            </Link>
            <span className="text-sm text-ink-soft">Free, no card, sample files included</span>
          </div>
        </div>
        <HeroLedger />
      </section>

      {/* Proof */}
      <section aria-label="Benchmark results" className="border-y border-rule py-12">
        <dl className="grid gap-8 md:grid-cols-3">
          {PROOF.map((p) => (
            <div key={p.value} className="grid gap-2">
              <dt className="order-2 text-sm text-ink-soft">{p.label}</dt>
              <dd className="order-1 font-mono text-4xl font-semibold tracking-tight">{p.value}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* Problem to solution */}
      <Reveal className="grid gap-6 py-24 md:grid-cols-2">
        <h2 className="text-3xl font-semibold tracking-tight md:text-4xl">
          Month end hides credit in a spreadsheet
        </h2>
        <div className="grid gap-4 text-lg text-ink-soft">
          <p>
            Input tax credit has to show up in the supplier&apos;s filings. Checking that by hand means
            sorting thousands of rows, where a stray slash in an invoice number or a supplier filing
            from its Pune branch looks exactly like a missing invoice.
          </p>
          <p className="text-ink">
            Milaan does the sorting. It normalises invoice numbers, recognises branches, and leaves your
            team the short list that genuinely needs a decision.
          </p>
        </div>
      </Reveal>

      {/* Benefits */}
      <section aria-labelledby="benefits-heading" className="grid gap-12 pb-24">
        <h2 id="benefits-heading" className="max-w-[680px] text-3xl font-semibold tracking-tight md:text-4xl">
          What your team gets on every run
        </h2>
        <div className="grid gap-x-12 gap-y-10 md:grid-cols-2 lg:grid-cols-3">
          {BENEFITS.map((b) => (
            <Reveal key={b.title} className="grid content-start gap-3">
              <b.icon size={28} weight="duotone" aria-hidden="true" />
              <h3 className="text-lg font-semibold">{b.title}</h3>
              <p className="text-base text-ink-soft">{b.body}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Tagline reveal */}
      <section aria-label="Why Milaan" className="py-24">
        <TaglineReveal
          lines={[
            "Spend month end on the 37 invoices",
            "that need judgement, not the 4,075",
            "that already agree.",
          ]}
        />
      </section>

      {/* How it works */}
      <section id="how" aria-labelledby="how-heading" className="grid scroll-mt-32 gap-12 py-24">
        <h2 id="how-heading" className="text-3xl font-semibold tracking-tight md:text-4xl">
          Three steps, one return period
        </h2>
        <ol className="grid gap-6 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <Reveal key={s.title}>
              <li className="grid h-full content-start gap-4 rounded-3xl border border-rule bg-sheet p-6">
                <span className="flex items-center justify-between">
                  <s.icon size={28} weight="duotone" aria-hidden="true" />
                  <span className="font-mono text-sm text-ink-soft">Step {i + 1}</span>
                </span>
                <h3 className="text-lg font-semibold">{s.title}</h3>
                <p className="text-base text-ink-soft">{s.body}</p>
              </li>
            </Reveal>
          ))}
        </ol>
      </section>

      {/* Verdicts */}
      <section id="verdicts" aria-labelledby="verdicts-heading" className="grid scroll-mt-32 gap-8 py-24 md:grid-cols-[1fr_1.4fr]">
        <div className="grid content-start gap-4">
          <h2 id="verdicts-heading" className="text-3xl font-semibold tracking-tight md:text-4xl">
            Four stamps, no guesswork
          </h2>
          <p className="text-lg text-ink-soft">
            Every invoice lands in exactly one of these. The rules behind them are in the open source
            matcher, so a partner can check why any row was stamped the way it was.
          </p>
        </div>
        <dl className="divide-y divide-rule rounded-3xl border border-rule bg-sheet">
          {VERDICTS.map((v) => (
            <div key={v.verdict} className="grid grid-cols-[7rem_1fr] items-center gap-4 p-6">
              <dt><VerdictStamp verdict={v.verdict} /></dt>
              <dd className="text-base">{v.meaning}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* FAQ */}
      <section id="faq" aria-labelledby="faq-heading" className="grid scroll-mt-32 gap-8 py-24 md:grid-cols-[1fr_1.4fr]">
        <div className="grid content-start gap-4">
          <h2 id="faq-heading" className="text-3xl font-semibold tracking-tight md:text-4xl">
            Questions partners ask first
          </h2>
          <div className="grid gap-2 text-sm">
            <span className="font-semibold">Synthetic sample files</span>
            <a className="underline underline-offset-4 hover:text-ink-soft" href="/samples/gstr2b_small.json" download>GSTR-2B JSON</a>
            <a className="underline underline-offset-4 hover:text-ink-soft" href="/samples/books_small.csv" download>Purchase register CSV</a>
            <a className="underline underline-offset-4 hover:text-ink-soft" href="/samples/abc101.pdf" download>Invoice PDF with a ₹70.00 gap</a>
          </div>
        </div>
        <div className="divide-y divide-rule rounded-3xl border border-rule bg-sheet">
          {FAQ.map((f) => (
            <details key={f.q} className="group p-6">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-lg font-semibold">
                {f.q}
                <span aria-hidden="true" className={`text-2xl text-ink-soft ${ui.motion} group-open:rotate-45`}>+</span>
              </summary>
              <p className="pt-3 text-base text-ink-soft">{f.a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="my-24 grid justify-items-start gap-6 rounded-3xl bg-ink p-8 text-paper md:p-16">
        <h2 className="max-w-[680px] text-4xl font-semibold tracking-tight md:text-5xl">
          Run this month&apos;s return through Milaan
        </h2>
        <p className="max-w-[680px] text-lg text-paper/75">
          Sign in with your email, add a client, and see every verdict in under a minute.
        </p>
        <Link
          href="/sign-in"
          className={`inline-flex items-center rounded-full bg-paper px-3 py-2 text-base font-semibold text-ink hover:bg-sheet active:scale-[0.98] ${ui.motion}`}
        >
          {CTA}
        </Link>
      </section>

      <footer className="flex flex-wrap items-center justify-between gap-4 border-t border-rule py-8 text-sm text-ink-soft">
        <span>Milaan reconciles GSTR-2B for Indian CA firms.</span>
        <nav aria-label="Footer" className="flex flex-wrap gap-6">
          <Link href="/privacy" className="hover:text-ink">Privacy</Link>
          <Link href="/terms" className="hover:text-ink">Terms</Link>
          <a href="https://github.com/dhairya-pandya/gst-2b-recon-agent" className="hover:text-ink">Source code</a>
        </nav>
      </footer>
    </main>
  );
}
