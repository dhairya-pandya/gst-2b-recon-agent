import { VerdictStamp, type Verdict } from "./verdict-stamp";

export type ReconEntry = {
  invoiceNo: string;
  date: string;
  taxable: string;
  tax: string;
};

export type AgentNote = {
  likely_cause: string;
  explanation: string;
  suggested_action: string;
  problems: string[];
};

export type { Decision } from "@/lib/reviews";
import type { Decision } from "@/lib/reviews";

type Props = {
  verdict: Verdict;
  gstr2b?: ReconEntry;
  book?: ReconEntry;
  reasons?: string[];
  agent?: AgentNote | null;
  decision?: Decision;
  onReview?: (d: Decision) => void;
  reviewBusy?: boolean;
};

const CAUSE: Record<string, string> = {
  format: "Invoice number format",
  typo: "Likely a typo",
  branch: "Supplier branch",
  timing: "Timing",
  amount: "Amount",
  unknown: "Unclear",
};

// Plain-language labels for the matcher's reason codes.
const REASON: Record<string, string> = {
  amount_gap: "Tax amounts differ",
  gstin_branch: "Supplier branch differs",
  date_out_of_window: "Date outside the period",
  invoice_total_mismatch: "Invoice PDF total differs",
  duplicate_in_books: "Repeated in the books",
};

export function reasonLabel(code: string): string {
  return REASON[code] ?? code.replaceAll("_", " ");
}

function Side({ entry, empty }: { entry?: ReconEntry; empty: string }) {
  if (!entry) {
    return <span className="text-caption opacity-70">{empty}</span>;
  }
  return (
    <div className="grid gap-0.5">
      <span className="font-semibold">{entry.invoiceNo}</span>
      <span className="text-caption">{entry.date}</span>
      <span className="text-right">
        {entry.taxable} + {entry.tax}
      </span>
    </div>
  );
}

export function ReconRow({
  verdict, gstr2b, book, reasons = [], agent, decision, onReview, reviewBusy,
}: Props) {
  const flagged = verdict !== "matched";
  return (
    <table className="w-full table-fixed border-collapse">
      <tbody>
        <tr className="border-b border-rule align-middle">
          <td className="w-[42%] p-3 align-top">
            <Side entry={gstr2b} empty="No 2B entry" />
          </td>
          <td className="w-[16%] p-3 text-center">
            <VerdictStamp verdict={verdict} />
            {reasons.length > 0 && (
              <ul className="mt-2 grid gap-0.5 text-caption">
                {reasons.map((r) => (
                  <li key={r}>{reasonLabel(r)}</li>
                ))}
              </ul>
            )}
          </td>
          <td className="w-[42%] p-3 align-top">
            <Side entry={book} empty="No book entry" />
          </td>
        </tr>
        {flagged && (agent || onReview) && (
          <tr className="border-b border-rule bg-paper">
            <td colSpan={3} className="px-3 pb-3 pt-2">
              <div className="grid gap-2 sm:grid-cols-[1fr_auto] sm:items-start">
                {agent ? (
                  <div className="grid gap-1 text-caption">
                    <p>
                      <span className="font-semibold">Agent note ({CAUSE[agent.likely_cause] ?? agent.likely_cause}):</span>{" "}
                      {agent.explanation}
                    </p>
                    <p><span className="font-semibold">Suggested:</span> {agent.suggested_action}</p>
                    {agent.problems.length > 0 && (
                      <p className="text-check">Critic: this note cites figures not in the source rows. Verify before acting.</p>
                    )}
                  </div>
                ) : (
                  <p className="text-caption opacity-70">No agent note for this row.</p>
                )}
                {onReview && (
                  <div className="flex items-center gap-2" role="group" aria-label="Review this row">
                    {decision && (
                      <span className="text-caption font-medium">
                        {decision === "accept" ? "Accepted" : "Rejected"}
                      </span>
                    )}
                    <button
                      type="button"
                      disabled={reviewBusy}
                      aria-pressed={decision === "accept"}
                      onClick={() => onReview("accept")}
                      className="rounded-full border border-matched px-3 py-1 text-caption text-matched hover:bg-matched hover:text-paper disabled:opacity-50"
                    >
                      Accept
                    </button>
                    <button
                      type="button"
                      disabled={reviewBusy}
                      aria-pressed={decision === "reject"}
                      onClick={() => onReview("reject")}
                      className="rounded-full border border-missing px-3 py-1 text-caption text-missing hover:bg-missing hover:text-paper disabled:opacity-50"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}
