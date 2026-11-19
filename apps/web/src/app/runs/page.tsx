"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { supabaseBrowser } from "@/lib/supabase/client";
import { ui } from "@/lib/ui";

// Magic-link and OAuth sign-ins land here with a one-time ?code= (PKCE).
// Exchange it for a session in the browser, then go to the new-run form.
// Without this step the page has no session and every request fails.
export default function RunsIndex() {
  const router = useRouter();
  const [failed, setFailed] = useState<string | null>(null);

  useEffect(() => {
    const url = new URL(window.location.href);
    const code = url.searchParams.get("code");
    const hasHashTokens = url.hash.includes("access_token");
    const supabase = supabaseBrowser();

    async function finish() {
      if (code) {
        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (error) {
          setFailed(`Code exchange failed: ${error.message}`);
          return;
        }
      }
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        setFailed(
          `No session found. code in link: ${code ? "yes" : "no"}; token in link: ${hasHashTokens ? "yes" : "no"}.`,
        );
        return;
      }
      router.replace("/runs/new");
    }

    void finish();
  }, [router]);

  if (failed) {
    return (
      <main className="mx-auto grid w-full max-w-md gap-4 px-8 py-12">
        <h1 className="text-4xl font-semibold tracking-tight">This sign-in link did not work</h1>
        <p className="text-body">Request a new sign-in link and open it in this same browser.</p>
        <p className={ui.hint}>{failed}</p>
        <div>
          <a href="/sign-in" className={ui.primary}>Back to sign in</a>
        </div>
      </main>
    );
  }

  return <p className="mx-auto w-full max-w-md px-8 py-12 text-body">Signing you in…</p>;
}
