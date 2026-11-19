"use client";

import { useEffect, useState } from "react";
import type { AgentNote, Decision } from "@/components/recon-row";
import { ReconTable, type RunRow } from "@/components/recon-table";
import { apiFetch } from "@/lib/api";
import { latestDecisions } from "@/lib/reviews";
import { supabaseBrowser } from "@/lib/supabase/client";
import { ui } from "@/lib/ui";

type RawEntry = { supplier_gstin: string; invoice_no: string; invoice_date: string;
  taxable_value: string; tax: Record<string, string> };

type RawRow = {
  verdict: RunRow["verdict"];
  reasons?: string[];
  gstr2b: null | RawEntry;
  book: null | RawEntry;
  agent?: AgentNote | null;
};

type RunMeta = {
  agent_status?: "off" | "none_flagged" | "complete" | "partial";
  reviews?: { row_key: string; decision: Decision }[];
};

const AGENT_STATUS: Record<string, string> = {
  off: "Agent notes are off for this run. Verdicts come from the deterministic matcher only.",
  none_flagged: "No rows needed an agent note.",
  complete: "Every flagged row has an agent note. Notes explain; they never change a verdict.",
  partial: "Some flagged rows have no agent note (the free Gemini quota allows a few per run). Verdicts are unaffected.",
};

function keyOf(r: RawRow): string | undefined {
  const src = r.gstr2b ?? r.book;
  return src ? `${src.supplier_gstin}|${src.invoice_no}` : undefined;
}


function toEntry(r: RawEntry | null) {
  if (!r) return undefined;
  const tax = Object.values(r.tax).reduce((a, b) => a + Number(b), 0);
  return {
    invoiceNo: r.invoice_no,
    date: r.invoice_date,
    taxable: Number(r.taxable_value).toFixed(2),
    tax: tax.toFixed(2),
  };
}

export default function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const [id, setId] = useState<string | null>(null);
  const [rows, setRows] = useState<RunRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [agentStatus, setAgentStatus] = useState<string>("off");
  const [decisions, setDecisions] = useState<Record<string, Decision>>({});
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);

  useEffect(() => {
    void params.then((p) => setId(p.id));
  }, [params]);

  useEffect(() => {
    if (!id) return;
    (async () => {
      const { data } = await supabaseBrowser().auth.getSession();
      const token = data.session?.access_token;
      if (!token) {
        setError("Sign in to view this run.");
        return;
      }
      setToken(token);
      try {
        const [meta, raw] = (await Promise.all([
          apiFetch(`/runs/${id}`, { token }),
          apiFetch(`/runs/${id}/rows`, { token }),
        ])) as [RunMeta, RawRow[]];
        setAgentStatus(meta.agent_status ?? "off");
        setDecisions(latestDecisions(meta.reviews));
        setRows(raw.map((r) => ({
          verdict: r.verdict,
          gstr2b: toEntry(r.gstr2b),
          book: toEntry(r.book),
          reasons: r.reasons ?? [],
          key: keyOf(r),
          agent: r.agent ?? null,
        })));
      } catch {
        setError("Could not load this run. Check that the run exists and try again.");
      }
    })();
  }, [id]);

  async function review(key: string, decision: Decision) {
    if (!token || !id) return;
    setBusyKey(key);
    setReviewError(null);
    try {
      await apiFetch(`/runs/${id}/reviews`, {
        token, method: "POST", json: { row_key: key, decision },
      });
      setDecisions((d) => ({ ...d, [key]: decision }));
    } catch {
      setReviewError("The decision was not saved. Try again.");
    } finally {
      setBusyKey(null);
    }
  }

  const flagged = rows?.filter((r) => r.verdict !== "matched").length ?? 0;
  const reviewed = rows?.filter((r) => r.verdict !== "matched" && r.key && decisions[r.key]).length ?? 0;

  return (
    <main className="mx-auto grid w-full max-w-5xl gap-6 px-8 py-12">
      <header className="grid gap-2">
        <h1 className={ui.heading}>Reconciliation</h1>
        {rows && (
          <p className="text-body">
            {rows.length} {rows.length === 1 ? "invoice" : "invoices"} compared.{" "}
            {flagged > 0 ? `${reviewed} of ${flagged} flagged ${flagged === 1 ? "row" : "rows"} reviewed.` : "Nothing to review."}
          </p>
        )}
        {rows && <p className={ui.hint}>{AGENT_STATUS[agentStatus] ?? AGENT_STATUS.off}</p>}
      </header>
      {!rows && !error && <p className="text-body">Loading reconciliation…</p>}
      {error && <p role="alert" className={ui.error}>{error}</p>}
      {rows && rows.length === 0 && (
        <p className={`${ui.panel} p-4 text-body`}>
          This run has no invoices. Check that the GSTR-2B and purchase register both contain rows for this period.
        </p>
      )}
      {reviewError && <p role="alert" className={ui.error}>{reviewError}</p>}
      {rows && rows.length > 0 && (
        <ReconTable rows={rows} decisions={decisions} onReview={review} busyKey={busyKey} />
      )}
    </main>
  );
}
