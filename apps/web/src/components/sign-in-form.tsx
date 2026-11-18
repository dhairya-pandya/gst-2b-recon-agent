"use client";

import { useState } from "react";
import { ui } from "@/lib/ui";

export type AuthClient = {
  signInWithOtp: (args: { email: string; options: { emailRedirectTo: string } }) => Promise<{ error: unknown }>;
  signInWithOAuth: (args: { provider: "google"; options: { redirectTo: string } }) => Promise<{ error: unknown }>;
};

export function SignInForm({ auth, redirectTo }: { auth: AuthClient; redirectTo: string }) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");

  async function google() {
    await auth.signInWithOAuth({ provider: "google", options: { redirectTo } });
  }

  async function magicLink(e: React.FormEvent) {
    e.preventDefault();
    setStatus("sending");
    const { error } = await auth.signInWithOtp({
      email,
      options: { emailRedirectTo: redirectTo },
    });
    setStatus(error ? "error" : "sent");
  }

  return (
    <main className="mx-auto grid w-full max-w-sm gap-6 px-8 py-12">
      <h1 className="text-display font-semibold">Sign in</h1>
      <button type="button" onClick={google} className={`${ui.secondary} text-left`}>
        Continue with Google
      </button>
      <div className="flex items-center gap-3 text-caption" aria-hidden="true">
        <span className="h-px flex-1 bg-rule" />
        or
        <span className="h-px flex-1 bg-rule" />
      </div>
      <form onSubmit={magicLink} className="grid gap-4">
        <label htmlFor="email" className={ui.field}>
          Work email
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            aria-describedby="email-hint"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={ui.input}
          />
        </label>
        <p id="email-hint" className={ui.hint}>
          We email a one-time link. There is no password to remember.
        </p>
        <button type="submit" disabled={status === "sending"} className={`${ui.primary} justify-self-start`}>
          {status === "sending" ? "Sending link…" : "Email me a sign-in link"}
        </button>
      </form>
      {status === "sent" && (
        <p role="status" className="text-body">
          Check your inbox for the sign-in link. It opens this app in the same browser.
        </p>
      )}
      {status === "error" && (
        <p role="alert" className={ui.error}>
          The link could not be sent. Check the address and try again.
        </p>
      )}
    </main>
  );
}
