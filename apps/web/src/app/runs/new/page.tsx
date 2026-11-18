"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { buildRunForm } from "@/lib/run-form";
import { supabaseBrowser } from "@/lib/supabase/client";
import { ui } from "@/lib/ui";

type Client = { id: string; name: string; gstin: string };

export default function NewRunPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [clients, setClients] = useState<Client[] | null>(null);
  const [clientId, setClientId] = useState("");
  const [period, setPeriod] = useState("");
  const [gstr2b, setGstr2b] = useState<File | null>(null);
  const [books, setBooks] = useState<File | null>(null);
  const [invoices, setInvoices] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void supabaseBrowser().auth.getSession().then(({ data }) => {
      setToken(data.session?.access_token ?? null);
    });
  }, []);

  useEffect(() => {
    if (!token) return;
    apiFetch("/clients", { token })
      .then((c) => setClients(c as Client[]))
      .catch(() => setError("Your clients could not be loaded. Refresh the page to try again."));
  }, [token]);

  async function start(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!token) return setError("Sign in before starting a reconciliation.");
    if (!gstr2b || !books) return setError("Add both the GSTR-2B file and the purchase register.");
    try {
      const body = buildRunForm({ clientId, period, gstr2b, books, invoices });
      setBusy(true);
      const res = (await apiFetch("/runs", { token, method: "POST", body })) as { run_id: string };
      router.push(`/runs/${res.run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The reconciliation could not start. Try again.");
      setBusy(false);
    }
  }

  const noClients = clients !== null && clients.length === 0;

  return (
    <main className="mx-auto grid w-full max-w-2xl gap-8 px-8 py-12">
      <header className="grid gap-2">
        <h1 className={ui.heading}>New reconciliation</h1>
        <p className="text-body">Upload one client&apos;s files for one return period.</p>
      </header>

      {noClients && (
        <p className={`${ui.panel} p-4 text-body`}>
          You have no clients yet. <Link href="/clients" className="font-medium underline">Add a client</Link> before starting a reconciliation.
        </p>
      )}

      <form onSubmit={start} className={`${ui.panel} grid gap-6 p-6`}>
        <label htmlFor="client" className={ui.field}>
          Client
          <select
            id="client"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            disabled={noClients}
            className={ui.input}
          >
            <option value="">Choose a client</option>
            {(clients ?? []).map((c) => (
              <option key={c.id} value={c.id}>{c.name} ({c.gstin})</option>
            ))}
          </select>
        </label>

        <label htmlFor="period" className={ui.field}>
          Return period
          <input
            id="period"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            placeholder="2026-11"
            aria-describedby="period-hint"
            className={`${ui.input} tabular-nums`}
          />
          <span id="period-hint" className={ui.hint}>Year and month, for example 2026-11.</span>
        </label>

        <label htmlFor="gstr2b" className={ui.field}>
          GSTR-2B file
          <input
            id="gstr2b"
            type="file"
            accept=".json"
            aria-describedby="gstr2b-hint"
            onChange={(e) => setGstr2b(e.target.files?.[0] ?? null)}
          />
          <span id="gstr2b-hint" className={ui.hint}>The JSON file downloaded from the GST portal.</span>
        </label>

        <label htmlFor="books" className={ui.field}>
          Purchase register
          <input
            id="books"
            type="file"
            accept=".csv"
            aria-describedby="books-hint"
            onChange={(e) => setBooks(e.target.files?.[0] ?? null)}
          />
          <span id="books-hint" className={ui.hint}>A CSV with the fixed column layout.</span>
        </label>

        <label htmlFor="invoices" className={ui.field}>
          Invoice PDFs (optional)
          <input
            id="invoices"
            type="file"
            multiple
            accept=".pdf"
            aria-describedby="invoices-hint"
            onChange={(e) => setInvoices(Array.from(e.target.files ?? []))}
          />
          <span id="invoices-hint" className={ui.hint}>
            Scanned PDFs without text are flagged for OCR rather than read.
          </span>
        </label>

        <div>
          <button type="submit" disabled={busy || noClients} className={ui.primary}>
            {busy ? "Starting…" : "Start reconciliation"}
          </button>
        </div>
        {error && <p role="alert" className={ui.error}>{error}</p>}
      </form>
    </main>
  );
}
