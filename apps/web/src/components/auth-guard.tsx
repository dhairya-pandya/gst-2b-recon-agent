"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { supabaseBrowser } from "@/lib/supabase/client";

// Pages that need a signed-in session. The API also checks the token on every request;
// this stops the pages themselves from opening without one.
const PROTECTED = ["/clients", "/runs/new", "/runs/"];

export function isProtected(pathname: string): boolean {
  return PROTECTED.some((p) => (p.endsWith("/") ? pathname.startsWith(p) : pathname === p));
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const needsAuth = isProtected(pathname);
  // null = checking, true = signed in, false = signed out (redirecting)
  const [signedIn, setSignedIn] = useState<boolean | null>(null);

  useEffect(() => {
    if (!needsAuth) return;
    let active = true;
    void supabaseBrowser().auth.getSession().then(({ data }) => {
      if (!active) return;
      setSignedIn(Boolean(data.session));
      if (!data.session) router.replace("/sign-in");
    });
    return () => {
      active = false;
    };
  }, [needsAuth, pathname, router]);

  if (!needsAuth) return <>{children}</>;
  if (signedIn !== true) {
    return <p className="mx-auto w-full max-w-md px-8 py-12 text-body">Checking your sign-in…</p>;
  }
  return <>{children}</>;
}
