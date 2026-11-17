"use client";

import { useState } from "react";

export type AuthClient = {
  signInWithOtp: (args: { email: string; options: { emailRedirectTo: string } }) => Promise<{ error: unknown }>;
  signInWithOAuth: (args: { provider: "google"; options: { redirectTo: string } }) => Promise<{ error: unknown }>;
};

export function SignInForm({ auth, redirectTo }: { auth: AuthClient; redirectTo: string }) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sent" | "error">("idle");

  async function google() {
    await auth.signInWithOAuth({ provider: "google", options: { redirectTo } });
  }

  async function magicLink(e: React.FormEvent) {
    e.preventDefault();
    const { error } = await auth.signInWithOtp({
      email,
      options: { emailRedirectTo: redirectTo },
    });
    setStatus(error ? "error" : "sent");
  }

  return (
    <div className="mx-auto grid w-full max-w-sm gap-6 p-8">
      <h1 className="text-display font-semibold">Sign in</h1>
      <button
        type="button"
        onClick={google}
        className="rounded-input border border-ink px-4 py-2 text-left"
      >
        Continue with Google
      </button>
      <form onSubmit={magicLink} className="grid gap-3">
        <label htmlFor="email" className="text-caption">Work email</label>
        <input
          id="email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-input border border-rule bg-white px-3 py-2"
        />
        <button type="submit" className="rounded-input bg-ink px-4 py-2 text-paper">
          Email me a sign-in link
        </button>
      </form>
      {status === "sent" && <p role="status">Check your email for a sign-in link.</p>}
      {status === "error" && <p role="alert">Could not send the link. Try again.</p>}
    </div>
  );
}
