"use client";

import { useEffect, useState } from "react";
import { ApiError, apiFetch } from "@/lib/api";
import { validateClientInput } from "@/lib/client-form";
import { supabaseBrowser } from "@/lib/supabase/client";
import { ui } from "@/lib/ui";

type Client = { id: string; name: string; gstin: string };

// Show what the API actually said, so the user knows whether to fix the form or sign in again.
function saveErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 401) return "Your sign-in has ended. Sign in again, then add the client.";
    const detail = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
    return `The client was not saved (HTTP ${err.status}: ${detail}).`;
  }
  return "The client was not saved. The API could not be reached. Try again.";
}

export default function ClientsPage() {
  const [token, setToken] = useState<string | null>(null);
  const [clients, setClients] = useState<Client[] | null>(null);
  const [name, setName] = useState("");
  const [gstin, setGstin] = useState("");
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

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!token) return setError("Sign in before adding a client.");
    const problem = validateClientInput({ name, gstin });
    if (problem) return setError(problem);
    setBusy(true);
    try {
      const created = (await apiFetch("/clients", {
        token,
        method: "POST",
        json: { name: name.trim(), gstin: gstin.trim().toUpperCase() },
      })) as Client;
      setClients((prev) => [...(prev ?? []), created]);
      setName("");
      setGstin("");
    } catch (err) {
      setError(saveErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto grid w-full max-w-3xl gap-10 px-8 py-12">
      <header className="grid gap-2">
        <h1 className={ui.heading}>Clients</h1>
        <p className="text-body">A client is a business whose GSTR-2B you reconcile.</p>
      </header>

      <section aria-labelledby="add-heading" className={`${ui.panel} grid gap-5 p-6`}>
        <h2 id="add-heading" className="font-semibold">Add a client</h2>
        <form onSubmit={add} className="grid gap-4 sm:grid-cols-2">
          <label htmlFor="client-name" className={ui.field}>
            Legal name
            <input
              id="client-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="organization"
              className={ui.input}
            />
          </label>
          <label htmlFor="client-gstin" className={ui.field}>
            GSTIN
            <input
              id="client-gstin"
              value={gstin}
              onChange={(e) => setGstin(e.target.value)}
              maxLength={15}
              aria-describedby="gstin-hint"
              className={`${ui.input} tabular-nums`}
            />
          </label>
          <p id="gstin-hint" className={`${ui.hint} sm:col-span-2`}>
            The 15-character GSTIN from the client&apos;s registration certificate.
          </p>
          <div className="sm:col-span-2">
            <button type="submit" disabled={busy} className={ui.primary}>
              {busy ? "Saving…" : "Save client"}
            </button>
          </div>
        </form>
        {error && <p role="alert" className={ui.error}>{error}</p>}
      </section>

      <section aria-labelledby="list-heading" className="grid gap-3">
        <h2 id="list-heading" className="font-semibold">Your clients</h2>
        {clients === null && !error && <p className="text-body">Loading clients…</p>}
        {clients?.length === 0 && (
          <p className={`${ui.panel} p-4 text-body`}>
            No clients yet. Add a client above, then start a reconciliation for them.
          </p>
        )}
        {clients && clients.length > 0 && (
          <ul className={`${ui.panel} divide-y divide-rule`}>
            {clients.map((c) => (
              <li key={c.id} className="flex flex-wrap justify-between gap-2 px-4 py-3">
                <span className="font-medium">{c.name}</span>
                <span className="tabular-nums">{c.gstin}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
