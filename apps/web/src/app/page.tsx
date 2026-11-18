import Link from "next/link";
import { VerdictStamp, type Verdict } from "@/components/verdict-stamp";
import { ui } from "@/lib/ui";

const KEY: { verdict: Verdict; meaning: string }[] = [
  { verdict: "matched", meaning: "Invoice number, date and every tax amount agree to within ₹1." },
  { verdict: "partial", meaning: "Amounts differ, or the supplier files under another branch. Review before claiming credit." },
  { verdict: "missing_in_2b", meaning: "The invoice is in one source only: the GSTR-2B or the purchase register." },
  { verdict: "duplicate", meaning: "The same invoice appears more than once in the purchase register." },
];

export default function Home() {
  return (
    <main className="mx-auto grid w-full max-w-3xl gap-10 px-8 py-12">
      <section className="grid gap-4">
        <h1 className="text-title font-semibold">Reconcile GSTR-2B against your books</h1>
        <p className="text-lead max-w-prose">
          Upload a client&apos;s GSTR-2B and purchase register. Every invoice gets a verdict,
          and anything that needs a decision is kept for review.
        </p>
        <div>
          <Link href="/sign-in" className={ui.primary}>
            Sign in to start
          </Link>
        </div>
      </section>

      <section aria-labelledby="key-heading" className="grid gap-4">
        <h2 id="key-heading" className={ui.heading}>What the verdicts mean</h2>
        <dl className={`${ui.panel} divide-y divide-rule`}>
          {KEY.map((k) => (
            <div key={k.verdict} className="grid grid-cols-[9rem_1fr] items-center gap-4 p-4">
              <dt>
                <VerdictStamp verdict={k.verdict} />
              </dt>
              <dd className="text-body">{k.meaning}</dd>
            </div>
          ))}
        </dl>
      </section>
    </main>
  );
}
