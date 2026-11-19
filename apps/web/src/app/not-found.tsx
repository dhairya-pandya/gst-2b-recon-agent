import Link from "next/link";
import { VerdictStamp } from "@/components/verdict-stamp";
import { ui } from "@/lib/ui";

export default function NotFound() {
  return (
    <main className="mx-auto grid w-full max-w-xl justify-items-start gap-6 px-6 py-24">
      <VerdictStamp verdict="missing_in_2b" />
      <h1 className="text-4xl font-semibold tracking-tight">This page is not in the register</h1>
      <p className="text-lg text-ink-soft">
        The link may be old, or the run may belong to another firm. Start from the home page.
      </p>
      <Link href="/" className={ui.primary}>Go to the home page</Link>
    </main>
  );
}
