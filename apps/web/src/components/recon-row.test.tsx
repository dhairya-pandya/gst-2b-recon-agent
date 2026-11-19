import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ReconRow, type ReconEntry } from "./recon-row";

const gstr: ReconEntry = {
  invoiceNo: "ABC/101",
  date: "05-11-2026",
  taxable: "1,000.00",
  tax: "180.00",
};
const book: ReconEntry = {
  invoiceNo: "abc-101",
  date: "05-11-2026",
  taxable: "1,000.00",
  tax: "180.00",
};

describe("ReconRow", () => {
  it("shows the 2B entry on the left and the book entry on the right", () => {
    render(<ReconRow verdict="matched" gstr2b={gstr} book={book} />);
    const cells = screen.getAllByRole("cell");
    expect(cells[0]).toHaveTextContent("ABC/101");
    expect(cells[1]).toHaveTextContent("Matched");
    expect(cells[2]).toHaveTextContent("abc-101");
  });

  it("shows an empty side when an entry is missing", () => {
    render(<ReconRow verdict="missing_in_books" gstr2b={gstr} />);
    expect(screen.getByText("No book entry")).toBeInTheDocument();
  });
});

describe("ReconRow reasons", () => {
  it("shows plain-language reasons under the stamp", () => {
    render(<ReconRow verdict="partial" gstr2b={gstr} book={book} reasons={["invoice_total_mismatch", "amount_gap"]} />);
    expect(screen.getByText("Invoice PDF total differs")).toBeInTheDocument();
    expect(screen.getByText("Tax amounts differ")).toBeInTheDocument();
  });

  it("shows the agent note and records a review on a flagged row", () => {
    const onReview = vi.fn();
    render(
      <ReconRow
        verdict="partial"
        gstr2b={gstr}
        book={book}
        agent={{ likely_cause: "amount", explanation: "PDF total differs.", suggested_action: "Ask the supplier.", problems: [] }}
        onReview={onReview}
      />,
    );
    expect(screen.getByText(/PDF total differs/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Accept" }));
    expect(onReview).toHaveBeenCalledWith("accept");
  });

  it("warns when the critic found problems", () => {
    render(
      <ReconRow
        verdict="partial"
        gstr2b={gstr}
        agent={{ likely_cause: "amount", explanation: "Gap of 999.", suggested_action: "Check.", problems: ["amount not in source: 999"] }}
      />,
    );
    expect(screen.getByText(/Verify before acting/)).toBeInTheDocument();
  });

  it("has no review controls on a matched row", () => {
    render(<ReconRow verdict="matched" gstr2b={gstr} book={book} onReview={() => {}} />);
    expect(screen.queryByRole("button", { name: "Accept" })).not.toBeInTheDocument();
  });
});
