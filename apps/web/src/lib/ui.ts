// Shared component classes. Colours and radii come from the tokens in app/globals.css.
export const ui = {
  field: "grid gap-1.5 text-body font-medium",
  hint: "text-caption font-normal opacity-75",
  input:
    "w-full rounded-input border border-rule bg-white px-3 py-2 font-normal placeholder:opacity-50",
  primary:
    "rounded-input bg-ink px-4 py-2 font-medium text-paper hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-50",
  secondary:
    "rounded-input border border-ink px-4 py-2 font-medium text-ink hover:bg-ink hover:text-paper",
  panel: "rounded-panel border border-rule bg-white",
  error: "text-body text-missing",
  heading: "text-heading font-semibold",
} as const;
