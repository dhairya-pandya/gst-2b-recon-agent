import { createBrowserClient } from "@supabase/ssr";

// Implicit flow: the magic link returns the session in the URL, so it works even when
// the link is opened in a different browser or app from the one that requested it.
// PKCE stores a verifier in the requesting browser only, which broke that case.
export function supabaseBrowser() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
    { auth: { flowType: "implicit" } },
  );
}
