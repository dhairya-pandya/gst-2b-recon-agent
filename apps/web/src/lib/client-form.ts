export type ClientInput = { name: string; gstin: string };

const GSTIN_RE = /^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/;

// Format check only. The API runs the full mod-36 checksum.
export function validateClientInput(input: ClientInput): string | null {
  if (input.name.trim().length < 2) return "Enter the client's legal name.";
  if (!GSTIN_RE.test(input.gstin.trim().toUpperCase())) {
    return "GSTIN must be 15 characters in the standard format.";
  }
  return null;
}
