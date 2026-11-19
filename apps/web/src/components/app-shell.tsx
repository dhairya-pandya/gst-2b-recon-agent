"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { supabaseBrowser } from "@/lib/supabase/client";

const NAV = [
  { href: "/clients", label: "Clients" },
  { href: "/runs/new", label: "New reconciliation" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  async function signOut() {
    await supabaseBrowser().auth.signOut();
    router.push("/sign-in");
  }

  return (
    <div className="flex min-h-full flex-col">
      <header className="border-b border-rule">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-8 py-4">
          <Link href="/" className="rounded-input font-semibold">
            GST 2B Recon
          </Link>
          <nav aria-label="Main" className="flex flex-wrap items-center gap-6">
            {NAV.map((item) => {
              const current = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={current ? "page" : undefined}
                  className={`border-b-2 pb-0.5 ${current ? "border-ink" : "border-transparent opacity-75 hover:opacity-100"}`}
                >
                  {item.label}
                </Link>
              );
            })}
            <button type="button" onClick={signOut} className="opacity-75 hover:opacity-100">
              Sign out
            </button>
          </nav>
        </div>
      </header>
      <div className="flex flex-1 flex-col">
        <AuthGuard>{children}</AuthGuard>
      </div>
    </div>
  );
}
