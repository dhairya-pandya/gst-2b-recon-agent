import { VerdictStamp, type Verdict } from "./verdict-stamp";

export type ReconEntry = {
  invoiceNo: string;
  date: string;
  taxable: string;
  tax: string;
};

type Props = {
  verdict: Verdict;
  gstr2b?: ReconEntry;
  book?: ReconEntry;
  reasons?: string[];
};

// Plain-language labels for the matcher's reason codes.
const REASON: Record<string, string> = {
  amount_gap: "Tax amounts differ",
  gstin_branch: "Supplier branch differs",
  date_out_of_window: "Date outside the period",
  invoice_total_mismatch: "Invoice PDF total differs",
  duplicate_in_books: "Repeated in the books",
};

export function reasonLabel(code: string): string {
  return REASON[code] ?? code.replaceAll("_", " ");
}

function Side({ entry, empty }: { entry?: ReconEntry; empty: string }) {
  if (!entry) {
    return <span className="text-caption opacity-70">{empty}</span>;
  }
  return (
    <div className="grid gap-0.5">
      <span className="font-semibold">{entry.invoiceNo}</span>
      <span className="text-caption">{entry.date}</span>
      <span className="text-right">
        {entry.taxable} + {entry.tax}
      </span>
    </div>
  );
}

export function ReconRow({ verdict, gstr2b, book, reasons = [] }: Props) {
  return (
    <table className="w-full table-fixed border-collapse">
      <tbody>
        <tr className="border-b border-rule align-middle">
          <td className="w-[42%] p-3 align-top">
            <Side entry={gstr2b} empty="No 2B entry" />
          </td>
          <td className="w-[16%] p-3 text-center">
            <VerdictStamp verdict={verdict} />
            {reasons.length > 0 && (
              <ul className="mt-2 grid gap-0.5 text-caption">
                {reasons.map((r) => (
                  <li key={r}>{reasonLabel(r)}</li>
                ))}
              </ul>
            )}
          </td>
          <td className="w-[42%] p-3 align-top">
            <Side entry={book} empty="No book entry" />
          </td>
        </tr>
      </tbody>
    </table>
  );
}
