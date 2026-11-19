"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth-guard";
import { Logo } from "@/components/logo";
import { supabaseBrowser } from "@/lib/supabase/client";
import { ui } from "@/lib/ui";

const APP_NAV = [
  { href: "/clients", label: "Clients" },
  { href: "/runs/new", label: "New reconciliation" },
];

const SITE_NAV = [
  { href: "/#how", label: "How it works" },
  { href: "/#verdicts", label: "Verdicts" },
  { href: "/#faq", label: "Questions" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [signedIn, setSignedIn] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const supabase = supabaseBrowser();
    void supabase.auth.getSession().then(({ data }) => setSignedIn(Boolean(data.session)));
    const { data } = supabase.auth.onAuthStateChange((_e, session) => setSignedIn(Boolean(session)));
    return () => data.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  async function signOut() {
    setOpen(false);
    await supabaseBrowser().auth.signOut();
    router.push("/sign-in");
  }

  const links = signedIn ? APP_NAV : SITE_NAV;

  return (
    <div className="flex min-h-full flex-col">
      <header className="sticky top-0 z-40 px-4">
        <div
          className={`relative z-50 mx-auto mt-6 flex w-full max-w-max items-center gap-4 rounded-full border border-rule bg-sheet/80 py-2 pl-4 pr-2 backdrop-blur-xl ${ui.motion}`}
        >
          <Link href={signedIn ? "/clients" : "/"} className="rounded-full" aria-label="Milaan home">
            <Logo />
          </Link>
          <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
            {links.map((item) => {
              const current = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={current ? "page" : undefined}
                  className={`rounded-full px-3 py-2 text-sm font-semibold ${ui.motion} ${
                    current ? "bg-ink text-paper" : "text-ink-soft hover:bg-paper hover:text-ink"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="hidden md:block">
            {signedIn ? (
              <button type="button" onClick={signOut} className={`${ui.secondary} px-3 py-2 text-sm`}>
                Sign out
              </button>
            ) : (
              <Link href="/sign-in" className={`${ui.primary} text-sm`}>
                Start reconciling
              </Link>
            )}
          </div>
          <button
            type="button"
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            aria-controls="mobile-menu"
            onClick={() => setOpen((o) => !o)}
            className="relative z-50 size-10 rounded-full md:hidden"
          >
            <span
              className={`absolute left-3 h-0.5 w-4 rounded-full bg-ink ${ui.motion} ${open ? "top-[19px] rotate-45" : "top-[15px]"}`}
            />
            <span
              className={`absolute left-3 h-0.5 w-4 rounded-full bg-ink ${ui.motion} ${open ? "top-[19px] -rotate-45" : "top-[23px]"}`}
            />
          </button>
        </div>
        <div
          id="mobile-menu"
          hidden={!open}
          className="fixed inset-0 z-40 bg-paper/80 px-8 pt-32 backdrop-blur-3xl md:hidden"
        >
          <nav aria-label="Mobile" className="grid gap-4">
            {[...links, ...(signedIn ? [] : [{ href: "/sign-in", label: "Sign in" }])].map((item, i) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                style={{ animationDelay: `${100 + i * 50}ms` }}
                className="menu-item text-3xl font-semibold"
              >
                {item.label}
              </Link>
            ))}
            {signedIn && (
              <button type="button" onClick={signOut} className="menu-item text-left text-3xl font-semibold">
                Sign out
              </button>
            )}
          </nav>
        </div>
      </header>
      <div id="main" className="flex flex-1 flex-col">
        <AuthGuard>{children}</AuthGuard>
      </div>
    </div>
  );
}
