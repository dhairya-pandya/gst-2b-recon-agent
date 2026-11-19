import { VerdictStamp, type Verdict } from "@/components/verdict-stamp";

type Row = { supplier: string; invoice: string; twoB: string; books: string; verdict: Verdict };

// Illustrative rows (synthetic suppliers), shaped exactly like a real run.
const ROWS: Row[] = [
  { supplier: "Kaveri Packaging Pvt Ltd", invoice: "KP/2026/0418", twoB: "11,846.40", books: "11,846.40", verdict: "matched" },
  { supplier: "Shree Balaji Steel", invoice: "SBS-1173", twoB: "13,216.00", books: "13,276.00", verdict: "partial" },
  { supplier: "Nilgiri Freight Carriers", invoice: "NFC/883", twoB: "4,071.90", books: "4,071.90", verdict: "matched" },
  { supplier: "Deccan Electricals", invoice: "DE/26/0092", twoB: "", books: "7,552.00", verdict: "missing_in_2b" },
  { supplier: "Kaveri Packaging Pvt Ltd", invoice: "KP/2026/0418", twoB: "", books: "11,846.40", verdict: "duplicate" },
];

export function HeroLedger() {
  return (
    <figure
      aria-label="Example reconciliation for November 2026"
      className="rounded-3xl border border-rule bg-sheet p-2"
    >
      <div className="rounded-2xl border border-rule">
        <figcaption className="flex flex-wrap items-baseline justify-between gap-2 border-b border-rule px-4 py-3">
          <span className="text-sm font-semibold">Sahyadri Agro Traders, November 2026</span>
          <span className="font-mono text-xs text-ink-soft">5 of 4,112 invoices</span>
        </figcaption>
        <table className="w-full text-left text-sm">
          <thead className="text-xs text-ink-soft">
            <tr>
              <th scope="col" className="px-4 py-2 font-medium">Supplier and invoice</th>
              <th scope="col" className="hidden px-2 py-2 text-right font-medium sm:table-cell">GSTR-2B ₹</th>
              <th scope="col" className="hidden px-2 py-2 text-right font-medium sm:table-cell">Books ₹</th>
              <th scope="col" className="px-4 py-2 text-right font-medium">Verdict</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((r, i) => (
              <tr key={i} className="border-t border-rule">
                <td className="px-4 py-3">
                  <span className="block font-semibold">{r.supplier}</span>
                  <span className="font-mono text-xs text-ink-soft">{r.invoice}</span>
                </td>
                <td className="hidden px-2 py-3 text-right font-mono sm:table-cell">{r.twoB || "None"}</td>
                <td className="hidden px-2 py-3 text-right font-mono sm:table-cell">{r.books}</td>
                <td className="px-4 py-3 text-right">
                  <span className="stamp-land inline-block" style={{ animationDelay: `${400 + i * 220}ms` }}>
                    <VerdictStamp verdict={r.verdict} />
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="border-t border-rule bg-paper px-4 py-3 text-xs text-ink-soft rounded-b-2xl">
          <span className="font-semibold text-check">Agent note on SBS-1173: </span>
          the books carry ₹60.00 more tax than the supplier filed. Ask Shree Balaji Steel for an amended invoice or correct the entry.
        </p>
      </div>
    </figure>
  );
}
