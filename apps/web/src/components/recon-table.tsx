"use client";

import { useMemo, useState } from "react";
import { ReconRow, type ReconEntry } from "./recon-row";
import { type Verdict } from "./verdict-stamp";

export type RunRow = {
  verdict: Verdict;
  gstr2b?: ReconEntry;
  book?: ReconEntry;
};

const FILTERS: { verdict: Verdict | "all"; label: string }[] = [
  { verdict: "all", label: "All" },
  { verdict: "matched", label: "Matched" },
  { verdict: "partial", label: "Check" },
  { verdict: "missing_in_2b", label: "Missing" },
  { verdict: "duplicate", label: "Duplicate" },
];

export function ReconTable({ rows }: { rows: RunRow[] }) {
  const [filter, setFilter] = useState<Verdict | "all">("all");

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const r of rows) c[r.verdict] = (c[r.verdict] ?? 0) + 1;
    return c;
  }, [rows]);

  const visible = filter === "all" ? rows : rows.filter((r) => r.verdict === filter);

  return (
    <section className="grid gap-4">
      <div role="toolbar" aria-label="Filter by verdict" className="flex flex-wrap gap-2">
        {FILTERS.map((f) => {
          const n =
            f.verdict === "all"
              ? rows.length
              : f.verdict === "missing_in_2b"
                ? (counts.missing_in_2b ?? 0) + (counts.missing_in_books ?? 0)
                : (counts[f.verdict] ?? 0);
          const pressed = filter === f.verdict;
          return (
            <button
              key={f.verdict}
              type="button"
              aria-pressed={pressed}
              onClick={() => setFilter(f.verdict)}
              className={`rounded-input border px-3 py-1 text-caption ${
                pressed ? "border-ink bg-ink text-paper" : "border-rule"
              }`}
            >
              {`${f.label} (${n})`}
            </button>
          );
        })}
      </div>
      <div className="rounded-panel border border-rule bg-white">
        {visible.map((r, i) => (
          <ReconRow
            key={i}
            verdict={r.verdict}
            gstr2b={r.gstr2b}
            book={r.book}
          />
        ))}
      </div>
    </section>
  );
}
