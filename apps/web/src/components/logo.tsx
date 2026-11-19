// Two overlapping rings: one record from the GSTR-2B, one from the books, meeting.
export function Logo({ withName = true }: { withName?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2 text-base font-bold tracking-tight">
      <svg viewBox="0 0 40 24" aria-hidden="true" className="h-6 w-10">
        <circle cx="13" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="3" />
        <circle cx="27" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="3" />
      </svg>
      {withName && <span>Milaan</span>}
    </span>
  );
}
