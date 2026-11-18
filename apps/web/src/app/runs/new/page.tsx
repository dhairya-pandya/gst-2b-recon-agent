"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { buildRunForm } from "@/lib/run-form";
import { supabaseBrowser } from "@/lib/supabase/client";

type Client = { id: string; name: string; gstin: string };

export default function NewRunPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
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
      .catch(() => setError("Could not load your clients."));
  }, [token]);

  async function start(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!token) return setError("Sign in to start a run.");
    if (!gstr2b || !books) return setError("Add both the GSTR-2B file and the purchase register.");
    try {
      const body = buildRunForm({ clientId, period, gstr2b, books, invoices });
      setBusy(true);
      const res = (await apiFetch("/runs", { token, method: "POST", body })) as { run_id: string };
      router.push(`/runs/${res.run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The run could not start.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto grid max-w-2xl gap-6 p-8">
      <h1 className="text-heading font-semibold">New reconciliation</h1>
      <form onSubmit={start} className="grid gap-4">
        <label className="grid gap-1 text-caption">
          Client
          <select
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            className="rounded-input border border-rule bg-white px-3 py-2 text-body"
          >
            <option value="">Choose a client</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>{c.name} ({c.gstin})</option>
            ))}
          </select>
        </label>
        <label className="grid gap-1 text-caption">
          Period (YYYY-MM)
          <input
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            placeholder="2026-11"
            className="rounded-input border border-rule bg-white px-3 py-2 text-body"
          />
        </label>
        <label className="grid gap-1 text-caption">
          GSTR-2B file (JSON)
          <input type="file" accept=".json" onChange={(e) => setGstr2b(e.target.files?.[0] ?? null)} />
        </label>
        <label className="grid gap-1 text-caption">
          Purchase register (CSV)
          <input type="file" accept=".csv" onChange={(e) => setBooks(e.target.files?.[0] ?? null)} />
        </label>
        <label className="grid gap-1 text-caption">
          Invoice PDFs (optional)
          <input
            type="file"
            multiple
            accept=".pdf"
            onChange={(e) => setInvoices(Array.from(e.target.files ?? []))}
          />
        </label>
        <button
          type="submit"
          disabled={busy}
          className="justify-self-start rounded-input bg-ink px-4 py-2 text-paper disabled:opacity-60"
        >
          Start reconciliation
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
    </main>
  );
}
