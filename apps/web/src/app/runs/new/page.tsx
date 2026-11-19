"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { FileField } from "@/components/file-field";
import { apiFetch } from "@/lib/api";
import { buildRunForm } from "@/lib/run-form";
import { supabaseBrowser } from "@/lib/supabase/client";
import { ui } from "@/lib/ui";

type Client = { id: string; name: string; gstin: string };

const PERIOD = /^\d{4}-\d{2}$/;

export default function NewRunPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [clients, setClients] = useState<Client[] | null>(null);
  const [clientId, setClientId] = useState("");
  const [period, setPeriod] = useState("");
  const [gstr2b, setGstr2b] = useState<File[]>([]);
  const [books, setBooks] = useState<File[]>([]);
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

  const noClients = clients !== null && clients.length === 0;
  const periodInvalid = period.length > 0 && !PERIOD.test(period);

  const missing: string[] = [];
  if (!clientId) missing.push("a client");
  if (!PERIOD.test(period)) missing.push("a return period");
  if (gstr2b.length === 0) missing.push("the GSTR-2B file");
  if (books.length === 0) missing.push("the purchase register");

  async function start(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!token) return setError("Sign in before starting a reconciliation.");
    if (missing.length > 0) return setError(`Still needed: ${missing.join(", ")}.`);
    try {
      const body = buildRunForm({
        clientId,
        period,
        gstr2b: gstr2b[0],
        books: books[0],
        invoices,
      });
      setBusy(true);
      const res = (await apiFetch("/runs", { token, method: "POST", body })) as { run_id: string };
      router.push(`/runs/${res.run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The reconciliation could not start. Try again.");
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto grid w-full max-w-2xl gap-8 px-8 py-12">
      <header className="grid gap-2">
        <h1 className="text-4xl font-semibold tracking-tight">New reconciliation</h1>
        <p className="text-body">Upload one client&apos;s files for one return period.</p>
      </header>

      {noClients && (
        <p className={`${ui.panel} p-4 text-body`}>
          You have no clients yet.{" "}
          <Link href="/clients" className="font-medium underline">Add a client</Link> before starting a reconciliation.
        </p>
      )}

      <form onSubmit={start} className={`${ui.panel} grid gap-6 p-6`} noValidate>
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
            aria-invalid={periodInvalid}
            aria-describedby="period-hint"
            className={`${ui.input} tabular-nums`}
          />
          <span id="period-hint" className={periodInvalid ? ui.error : ui.hint}>
            {periodInvalid ? "Use the year and month, for example 2026-11." : "Year and month, for example 2026-11."}
          </span>
        </label>

        <FileField
          label="GSTR-2B file"
          hint="The JSON file downloaded from the GST portal."
          accept=".json"
          files={gstr2b}
          onChange={setGstr2b}
        />

        <FileField
          label="Purchase register"
          hint="A CSV with the fixed column layout."
          accept=".csv"
          files={books}
          onChange={setBooks}
        />

        <FileField
          label="Invoice PDFs (optional)"
          hint="Scanned PDFs without text are flagged for OCR rather than read."
          accept=".pdf"
          files={invoices}
          onChange={setInvoices}
          multiple
        />

        <div className="grid gap-2">
          <div>
            <button type="submit" disabled={busy || noClients || missing.length > 0} className={ui.primary}>
              {busy ? "Starting…" : "Start reconciliation"}
            </button>
          </div>
          {missing.length > 0 && !busy && (
            <p className={ui.hint}>Still needed: {missing.join(", ")}.</p>
          )}
        </div>
        {error && <p role="alert" className={ui.error}>{error}</p>}
      </form>
    </main>
  );
}
