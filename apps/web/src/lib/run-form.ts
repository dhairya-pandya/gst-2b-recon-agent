export type RunInput = {
  clientId: string;
  period: string; // "YYYY-MM"
  gstr2b: File;
  books: File;
  invoices: File[];
};

export function buildRunForm(input: RunInput): FormData {
  if (!input.clientId) throw new Error("Choose a client before starting a run.");
  if (!/^\d{4}-\d{2}$/.test(input.period)) throw new Error("Enter the period as YYYY-MM.");
  const fd = new FormData();
  fd.append("client_id", input.clientId);
  fd.append("period", input.period);
  fd.append("gstr2b", input.gstr2b);
  fd.append("books", input.books);
  for (const f of input.invoices) fd.append("invoices", f);
  return fd;
}
