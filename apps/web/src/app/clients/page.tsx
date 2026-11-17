"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { validateClientInput } from "@/lib/client-form";
import { supabaseBrowser } from "@/lib/supabase/client";

type Client = { id: string; name: string; gstin: string };

export default function ClientsPage() {
  const [token, setToken] = useState<string | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
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
      .catch(() => setError("Could not load your clients."));
  }, [token]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!token) return setError("Sign in to add a client.");
    const problem = validateClientInput({ name, gstin });
    if (problem) return setError(problem);
    setBusy(true);
    try {
      const created = (await apiFetch("/clients", {
        token,
        method: "POST",
        json: { name: name.trim(), gstin: gstin.trim().toUpperCase() },
      })) as Client;
      setClients((prev) => [...prev, created]);
      setName("");
      setGstin("");
    } catch {
      setError("The client could not be saved. Check the GSTIN and try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto grid max-w-2xl gap-8 p-8">
      <h1 className="text-heading font-semibold">Clients</h1>
      <form onSubmit={add} className="grid gap-4">
        <label className="grid gap-1 text-caption">
          Legal name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="rounded-input border border-rule bg-white px-3 py-2 text-body"
          />
        </label>
        <label className="grid gap-1 text-caption">
          GSTIN
          <input
            value={gstin}
            onChange={(e) => setGstin(e.target.value)}
            maxLength={15}
            className="rounded-input border border-rule bg-white px-3 py-2 text-body tabular-nums"
          />
        </label>
        <button
          type="submit"
          disabled={busy}
          className="justify-self-start rounded-input bg-ink px-4 py-2 text-paper disabled:opacity-60"
        >
          Add client
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      <ul className="grid gap-2">
        {clients.map((c) => (
          <li key={c.id} className="flex justify-between rounded-panel border border-rule bg-white px-4 py-3">
            <span>{c.name}</span>
            <span className="tabular-nums">{c.gstin}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
