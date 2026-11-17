export type Verdict = "matched" | "partial" | "missing_in_2b" | "missing_in_books" | "duplicate";

const LABEL: Record<Verdict, string> = {
  matched: "Matched",
  partial: "Check",
  missing_in_2b: "Missing",
  missing_in_books: "Missing",
  duplicate: "Duplicate",
};

const INK: Record<Verdict, string> = {
  matched: "text-matched border-matched",
  partial: "text-check border-check",
  missing_in_2b: "text-missing border-missing",
  missing_in_books: "text-missing border-missing",
  duplicate: "text-missing border-missing",
};

export function VerdictStamp({ verdict }: { verdict: Verdict }) {
  return (
    <span
      data-verdict={verdict}
      className={`inline-block -rotate-4 rounded-stamp border-2 border-double px-3 py-0.5 text-caption font-semibold ${INK[verdict]}`}
    >
      {LABEL[verdict]}
    </span>
  );
}
