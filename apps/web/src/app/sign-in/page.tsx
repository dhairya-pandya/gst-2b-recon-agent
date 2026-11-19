"use client";

import { useSyncExternalStore } from "react";
import { type AuthClient, SignInForm } from "@/components/sign-in-form";
import { supabaseBrowser } from "@/lib/supabase/client";

// Browser-only values: null on the server, filled in on the client. The Supabase
// client is created once, lazily, so prerendering works without the env vars.
let cachedAuth: AuthClient | null = null;
const noop = () => () => {};

function getAuth(): AuthClient {
  cachedAuth ??= supabaseBrowser().auth as unknown as AuthClient;
  return cachedAuth;
}

export default function SignInPage() {
  const auth = useSyncExternalStore<AuthClient | null>(noop, getAuth, () => null);
  const origin = useSyncExternalStore(noop, () => window.location.origin, () => "");

  if (!auth) return <p className="p-8">Loading sign-in…</p>;
  return (
    <SignInForm
      auth={auth}
      redirectTo={`${origin}/runs`}
      google={process.env.NEXT_PUBLIC_GOOGLE_SIGN_IN === "true"}
    />
  );
}
