"use client";

import { useMemo, useState } from "react";
import { ReconRow, type ReconEntry } from "./recon-row";
import { type Verdict } from "./verdict-stamp";
import { ui } from "@/lib/ui";

export type RunRow = {
  verdict: Verdict;
  gstr2b?: ReconEntry;
  book?: ReconEntry;
  reasons?: string[];
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
                pressed ? "border-ink bg-ink font-medium text-paper" : "border-rule hover:border-ink"
              }`}
            >
              {`${f.label} (${n})`}
            </button>
          );
        })}
      </div>
      <div className={ui.panel}>
        <div
          role="presentation"
          className="grid grid-cols-[42%_16%_42%] border-b border-rule px-3 py-2 text-caption font-medium"
        >
          <span>2B entry</span>
          <span className="text-center">Verdict</span>
          <span>Book entry</span>
        </div>
        {visible.length === 0 ? (
          <p className="p-4 text-body">No invoices have this verdict in this run.</p>
        ) : (
          visible.map((r, i) => (
            <ReconRow key={i} verdict={r.verdict} gstr2b={r.gstr2b} book={r.book} reasons={r.reasons} />
          ))
        )}
      </div>
    </section>
  );
}
