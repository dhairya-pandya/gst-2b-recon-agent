"use client";

import { useState } from "react";
import { ui } from "@/lib/ui";

export type AuthClient = {
  signInWithOtp: (args: {
    email: string;
    options: { emailRedirectTo: string };
  }) => Promise<{ error: unknown }>;
  signInWithOAuth: (args: {
    provider: "google";
    options: { redirectTo: string };
  }) => Promise<{ error: unknown }>;
};

// Google sign-in needs an OAuth client in Supabase; the button only shows once that exists.
export function SignInForm({
  auth,
  redirectTo,
  google: googleEnabled = false,
}: {
  auth: AuthClient;
  redirectTo: string;
  google?: boolean;
}) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">(
    "idle",
  );

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
    <main className="mx-auto grid w-full max-w-md gap-6 px-6 py-16">
      <div className="grid gap-2">
        <h1 className="text-4xl font-semibold tracking-tight">
          Sign in to Milaan
        </h1>
        <p className="text-base text-ink-soft">
          New here? The same link creates your account. Try it with the
          synthetic sample files on the home page.
        </p>
      </div>
      <div className="grid gap-6 rounded-3xl border border-rule bg-sheet p-6">
        {googleEnabled && (
          <>
            <button type="button" onClick={google} className={ui.secondary}>
              Continue with Google
            </button>
            <div className="flex items-center gap-3 text-xs" aria-hidden="true">
              <span className="h-px flex-1 bg-rule" />
              or
              <span className="h-px flex-1 bg-rule" />
            </div>
          </>
        )}
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
            We email a one time link. There is no password to remember.
          </p>
          <button
            type="submit"
            disabled={status === "sending"}
            className={`${ui.primary} justify-self-start`}
          >
            {status === "sending" ? "Sending link…" : "Email me a sign-in link"}
          </button>
        </form>
      </div>
      {status === "sent" && (
        <p role="status" className="text-body">
          Check your inbox for the sign-in link. It opens this app in the same
          browser.
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
