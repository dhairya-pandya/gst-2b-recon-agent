"use client";

import { useEffect, useState } from "react";
import { ReconTable, type RunRow } from "@/components/recon-table";
import { apiFetch } from "@/lib/api";
import { supabaseBrowser } from "@/lib/supabase/client";

type RawRow = {
  verdict: RunRow["verdict"];
  gstr2b: null | { invoice_no: string; invoice_date: string; taxable_value: string;
    tax: Record<string, string> };
  book: null | { invoice_no: string; invoice_date: string; taxable_value: string;
    tax: Record<string, string> };
};

function toEntry(r: RawRow["gstr2b"]) {
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
      try {
        const raw = (await apiFetch(`/runs/${id}/rows`, { token })) as RawRow[];
        setRows(raw.map((r) => ({
          verdict: r.verdict,
          gstr2b: toEntry(r.gstr2b),
          book: toEntry(r.book),
        })));
      } catch {
        setError("Could not load this run. Check that the run exists and try again.");
      }
    })();
  }, [id]);

  return (
    <main className="mx-auto grid max-w-5xl gap-6 p-8">
      <h1 className="text-heading font-semibold">Reconciliation</h1>
      {error && <p role="alert">{error}</p>}
      {rows && <ReconTable rows={rows} />}
    </main>
  );
}
