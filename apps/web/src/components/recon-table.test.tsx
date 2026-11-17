import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReconTable, type RunRow } from "./recon-table";

const rows: RunRow[] = [
  {
    verdict: "matched",
    gstr2b: { invoiceNo: "ABC/101", date: "05-11-2026", taxable: "1,000.00", tax: "180.00" },
    book: { invoiceNo: "abc-101", date: "05-11-2026", taxable: "1,000.00", tax: "180.00" },
  },
  {
    verdict: "partial",
    gstr2b: { invoiceNo: "ABC/102", date: "07-11-2026", taxable: "2,000.00", tax: "360.00" },
    book: { invoiceNo: "ABC/102", date: "07-11-2026", taxable: "2,000.00", tax: "356.00" },
  },
];

describe("ReconTable", () => {
  it("shows every row by default", () => {
    render(<ReconTable rows={rows} />);
    expect(screen.getAllByRole("row")).toHaveLength(2);
  });

  it("filters to one verdict from the filter bar", () => {
    render(<ReconTable rows={rows} />);
    fireEvent.click(screen.getByRole("button", { name: /^Check/ }));
    expect(screen.getAllByRole("row")).toHaveLength(1);
    expect(screen.getAllByText("ABC/102")).toHaveLength(2); // 2B side and book side
  });

  it("shows the count next to each filter", () => {
    render(<ReconTable rows={rows} />);
    expect(screen.getByRole("button", { name: "Matched (1)" })).toBeInTheDocument();
  });
});
