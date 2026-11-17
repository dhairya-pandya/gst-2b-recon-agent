import { VerdictStamp } from "@/components/verdict-stamp";

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-title font-semibold">GST 2B Recon</h1>
      <p className="mt-2 text-lead">Reconcile GSTR-2B against the purchase register.</p>
      <div className="mt-6 flex gap-3">
        <VerdictStamp verdict="matched" />
        <VerdictStamp verdict="partial" />
        <VerdictStamp verdict="missing_in_2b" />
        <VerdictStamp verdict="duplicate" />
      </div>
    </main>
  );
}
