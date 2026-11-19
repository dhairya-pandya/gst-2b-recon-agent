// Shared component classes. Colours and radii come from the tokens in app/globals.css.
const motion = "transition-all duration-700 ease-[cubic-bezier(0.32,0.72,0,1)]";

export const ui = {
  field: "grid gap-2 text-sm font-semibold",
  hint: "text-xs font-normal text-ink-soft",
  input: `w-full rounded-input border border-rule bg-sheet px-3 py-2 text-base font-normal placeholder:text-ink-soft/60 hover:border-ink-soft ${motion}`,
  primary: `inline-flex items-center justify-center gap-2 rounded-full bg-ink px-3 py-2 text-base font-semibold text-paper hover:bg-ink-soft active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100 ${motion}`,
  secondary: `inline-flex items-center justify-center gap-2 rounded-full border border-ink px-3 py-2 text-base font-semibold text-ink hover:bg-ink hover:text-paper active:scale-[0.98] ${motion}`,
  panel: "rounded-panel border border-rule bg-sheet",
  error: "text-sm text-missing",
  heading: "text-2xl font-semibold",
  motion,
} as const;
