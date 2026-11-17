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
};

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

export function ReconRow({ verdict, gstr2b, book }: Props) {
  return (
    <table className="w-full table-fixed border-collapse">
      <tbody>
        <tr className="border-b border-rule align-middle">
          <td className="w-[42%] p-3 align-top">
            <Side entry={gstr2b} empty="No 2B entry" />
          </td>
          <td className="w-[16%] p-3 text-center">
            <VerdictStamp verdict={verdict} />
          </td>
          <td className="w-[42%] p-3 align-top">
            <Side entry={book} empty="No book entry" />
          </td>
        </tr>
      </tbody>
    </table>
  );
}
