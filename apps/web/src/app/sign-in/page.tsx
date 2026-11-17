"use client";

import { SignInForm } from "@/components/sign-in-form";
import { supabaseBrowser } from "@/lib/supabase/client";

export default function SignInPage() {
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  return <SignInForm auth={supabaseBrowser().auth} redirectTo={`${origin}/runs`} />;
}
